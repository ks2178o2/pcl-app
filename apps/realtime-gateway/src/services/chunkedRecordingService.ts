// ChunkedRecordingManager.ts
// ✅ Resilient chunked recorder: timeslices + IndexedDB persistence + lifecycle guards
// - Flushes small audio slices every 5s to IndexedDB so a tab discard/reload won’t lose in-flight audio
// - Reassembles unfinished chunk on restore and uploads it before resuming
// - Finalizes current slice on visibility/pagehide to minimize loss window

export interface ChunkInfo {
  id: string;
  callRecordId: string;
  chunkNumber: number;
  audioBlob: Blob;
  duration: number; // seconds
  fileSize: number; // bytes
  uploadStatus: "pending" | "uploading" | "completed" | "failed";
  retryCount: number;
}

export interface RecordingProgress {
  currentChunk: number;
  totalChunks: number;
  chunksUploaded: number;
  chunksFailed: number;
  isRecording: boolean;
  isComplete: boolean;
  totalDuration: number; // seconds
  audioLevel?: number;
  errorMessage?: string;
}

interface PersistedRecordingState {
  callRecordId: string;
  currentChunkNumber: number;
  totalStartTime: number; // epoch ms
  isRecording: boolean;
  lastUpdateTime: number; // epoch ms
  lastSaveTime?: number; // epoch ms - for tracking background duration
  totalChunks: number; // completed chunks known in memory
  currentChunkStartTime?: number; // epoch ms
  currentSliceSeq?: number;
}

/* ----------------------------- IndexedDB helper ---------------------------- */

class SliceStore {
  private dbp: Promise<IDBDatabase>;
  constructor() {
    this.dbp = new Promise((resolve, reject) => {
      const req = indexedDB.open("chunked-audio", 1);
      req.onupgradeneeded = () => {
        const db = req.result;
        if (!db.objectStoreNames.contains("slices")) {
          // key = `${callId}|${chunkNo}|${seq}`
          db.createObjectStore("slices", { keyPath: "key" });
        }
        if (!db.objectStoreNames.contains("meta")) {
          db.createObjectStore("meta", { keyPath: "key" });
        }
      };
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
  }
  async putSlice(callId: string, chunkNo: number, seq: number, blob: Blob) {
    const key = `${callId}|${chunkNo}|${seq}`;
    const db = await this.dbp;
    const tx = db.transaction("slices", "readwrite");
    tx.objectStore("slices").put({ key, callId, chunkNo, seq, blob });
    await new Promise<void>((res, rej) => {
      tx.oncomplete = () => res();
      tx.onerror = () => rej(tx.error);
      tx.onabort = () => rej(tx.error);
    });
  }
  async getSlices(callId: string, chunkNo: number): Promise<{ seq: number; blob: Blob }[]> {
    const db = await this.dbp;
    const tx = db.transaction("slices", "readonly");
    const store = tx.objectStore("slices");
    const range = IDBKeyRange.bound(`${callId}|${chunkNo}|`, `${callId}|${chunkNo}|~`);
    const out: { seq: number; blob: Blob }[] = [];
    await new Promise<void>((res, rej) => {
      const req = store.openCursor(range);
      req.onsuccess = () => {
        const cur = req.result;
        if (!cur) return res();
        const v = cur.value as { seq: number; blob: Blob };
        out.push({ seq: v.seq, blob: v.blob });
        cur.continue();
      };
      req.onerror = () => rej(req.error);
    });
    out.sort((a, b) => a.seq - b.seq);
    return out;
  }
  async clearGroup(callId: string, chunkNo: number) {
    const db = await this.dbp;
    const tx = db.transaction("slices", "readwrite");
    const store = tx.objectStore("slices");
    const range = IDBKeyRange.bound(`${callId}|${chunkNo}|`, `${callId}|${chunkNo}|~`);
    await new Promise<void>((res, rej) => {
      const req = store.openCursor(range);
      req.onsuccess = () => {
        const cur = req.result;
        if (!cur) return res();
        cur.delete();
        cur.continue();
      };
      req.onerror = () => rej(req.error);
    });
    await new Promise<void>((res, rej) => {
      tx.oncomplete = () => res();
      tx.onerror = () => rej(tx.error);
      tx.onabort = () => rej(tx.error);
    });
  }
}

const sliceStore = new SliceStore();

/* ------------------------- ChunkedRecordingManager ------------------------- */

export class ChunkedRecordingManager {
  private mediaRecorder: MediaRecorder | null = null;
  private currentChunkNumber = 0;
  private chunks: ChunkInfo[] = [];
  private callRecordId: string | null = null;

  // 5 minutes per server chunk; slices every 5s
  private chunkDuration = 5 * 60 * 1000; // ms
  private sliceDuration = 5 * 1000; // ms

  private onProgressUpdate?: (progress: RecordingProgress) => void;
  private stream: MediaStream | null = null;
  private chunkStartTime = 0;
  private totalStartTime = 0;
  private isRecording = false;
  private recordingComplete = false;
  private progressUpdateInterval: number | null = null;

  // Live audio monitoring
  private audioContext: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private audioLevel = 0;
  private audioLevelRaf: number | null = null;

  // in-flight sequence for the current chunk's slices
  private currentSliceSeq = 0;

  private _chunkHardStopTimer: number | null = null;
  private _lifecycleBound = false;
  private _unsub: Array<() => void> = [];

  private static readonly STORAGE_KEY = "chunked_recording_state";

  constructor(onProgressUpdate?: (progress: RecordingProgress) => void) {
    this.onProgressUpdate = onProgressUpdate;
  }

  /* -------------------------- Persistence (metadata) -------------------------- */

  public saveState(): void {
    if (!this.callRecordId) return;

    const state: PersistedRecordingState = {
      callRecordId: this.callRecordId,
      currentChunkNumber: this.currentChunkNumber,
      totalStartTime: this.totalStartTime,
      isRecording: this.isRecording,
      lastUpdateTime: Date.now(),
      lastSaveTime: Date.now(), // Add this for accurate background tracking
      totalChunks: this.chunks.length,
      currentChunkStartTime: this.chunkStartTime,
      currentSliceSeq: this.currentSliceSeq,
    };

    try {
      localStorage.setItem(ChunkedRecordingManager.STORAGE_KEY, JSON.stringify(state));
    } catch (error) {
      console.error("Failed to save recording state:", error);
    }
  }

  static loadState(): PersistedRecordingState | null {
    try {
      const stateJson = localStorage.getItem(ChunkedRecordingManager.STORAGE_KEY);
      if (!stateJson) return null;

      const state = JSON.parse(stateJson) as PersistedRecordingState;
      const hoursSinceUpdate = (Date.now() - state.lastUpdateTime) / (1000 * 60 * 60);
      if (hoursSinceUpdate > 24) {
        ChunkedRecordingManager.clearState();
        return null;
      }
      return state;
    } catch (error) {
      console.error("Failed to load recording state:", error);
      return null;
    }
  }

  static clearState(): void {
    try {
      localStorage.removeItem(ChunkedRecordingManager.STORAGE_KEY);
    } catch (error) {
      console.error("Failed to clear recording state:", error);
    }
  }

  static validateState(state: PersistedRecordingState | null): { valid: boolean; reason?: string } {
    if (!state) return { valid: false, reason: 'No state found' };
    
    // Check age of state
    const stateAgeMs = Date.now() - state.lastUpdateTime;
    const stateAgeMinutes = stateAgeMs / (1000 * 60);
    
    // If state is older than 15 minutes, consider it stale
    if (stateAgeMinutes > 15) {
      return { valid: false, reason: `State is ${Math.floor(stateAgeMinutes)} minutes old` };
    }
    
    // If state says recording but no chunks were created, likely interrupted early
    if (state.isRecording && state.totalChunks === 0 && stateAgeMinutes > 5) {
      return { valid: false, reason: 'Recording never produced chunks' };
    }
    
    return { valid: true };
  }

  static async clearAllSlices(): Promise<void> {
    try {
      const dbp = indexedDB.open("chunked-audio", 1);
      const db = await new Promise<IDBDatabase>((resolve, reject) => {
        dbp.onsuccess = () => resolve(dbp.result);
        dbp.onerror = () => reject(dbp.error);
        dbp.onupgradeneeded = () => {
          const db = dbp.result;
          if (!db.objectStoreNames.contains("slices")) {
            db.createObjectStore("slices", { keyPath: "key" });
          }
          if (!db.objectStoreNames.contains("meta")) {
            db.createObjectStore("meta", { keyPath: "key" });
          }
        };
      });
      
      const tx = db.transaction(["slices", "meta"], "readwrite");
      tx.objectStore("slices").clear();
      tx.objectStore("meta").clear();
      
      await new Promise<void>((resolve, reject) => {
        tx.oncomplete = () => resolve();
        tx.onerror = () => reject(tx.error);
      });
      
      db.close();
      console.log('✅ Cleared all IndexedDB recording slices');
    } catch (error) {
      console.warn('⚠️ Could not clear IndexedDB slices:', error);
    }
  }

  /* --------------------------- Lifecycle protections -------------------------- */

  private bindLifecycleGuards() {
    if (this._lifecycleBound) return;
    this._lifecycleBound = true;

    const finalizeNow = async () => {
      try {
        if (this.mediaRecorder?.state === "recording") {
          try {
            this.mediaRecorder.requestData();
          } catch {}
          this.mediaRecorder.stop();
        }
        this.saveState();
      } catch {}
    };

    const vis = () => {
      if (document.visibilityState === "hidden") {
        // KEEP RECORDING IN BACKGROUND - just flush current data and save state
        try {
          this.mediaRecorder?.requestData();
        } catch {}
        // Save state with current timestamp for accurate background duration tracking
        this.saveState();
        console.log('👁️ Tab hidden - flushed data and saved state');
      } else if (document.visibilityState === "visible") {
        // Tab became visible again
        console.log('👁️ Tab visible - recording continues, flushing any buffered data');
        
        // Immediately flush any buffered audio data
        if (this.isRecording && this.mediaRecorder?.state === "recording") {
          try {
            this.mediaRecorder.requestData();
          } catch (e) {
            console.error('Failed to flush audio data on visibility:', e);
          }
        }
        
        // Retry failed uploads
        this.retryFailedChunks().catch(console.error);
        
        // If current chunk has exceeded duration while hidden, finalize it now
        if (this.isRecording && this.mediaRecorder?.state === "recording" && this.chunkStartTime > 0) {
          const elapsed = Date.now() - this.chunkStartTime;
          if (elapsed >= this.chunkDuration) {
            console.log(`⏱️ Chunk exceeded duration (${elapsed}ms) while hidden, finalizing now`);
            try { 
              this.mediaRecorder.requestData(); 
            } catch {}
            this.mediaRecorder.stop(); // This will trigger onstop → upload → start next chunk
          }
        }
        
        // Update UI progress
        this.updateProgress();
      }
    };
    const ph = () => finalizeNow();

    document.addEventListener("visibilitychange", vis);
    window.addEventListener("pagehide", ph, { capture: true });

    this._unsub.push(() => document.removeEventListener("visibilitychange", vis));
    this._unsub.push(() => window.removeEventListener("pagehide", ph, { capture: true } as any));

    // Ask for persistent storage to reduce eviction chance (best-effort)
    if ((navigator as any).storage?.persist) {
      (navigator as any).storage
        .persist()
        .then((persisted: boolean) => {
          console.log("Persistent storage:", persisted ? "granted" : "not granted");
        })
        .catch(() => {});
    }
  }

  /* --------------------------- Restore from persisted -------------------------- */

  async restoreFromState(state: PersistedRecordingState): Promise<boolean> {
    try {
      console.log("🔄 Restoring recording from saved state:", state);

      const { supabase } = await import("@/integrations/supabase/client");

      // CRITICAL: Verify the call_records entry exists and belongs to current user
      // This prevents RLS violations when uploading chunks after restoration
      const { data: callRecord, error: callRecordError } = await supabase
        .from("call_records")
        .select("id, user_id, recording_complete, total_chunks, chunks_uploaded")
        .eq("id", state.callRecordId)
        .single();

      if (callRecordError || !callRecord) {
        console.error("❌ Call record not found or inaccessible:", callRecordError);
        throw new Error("Cannot restore recording - call record not found or you don't have access");
      }

      // Verify user owns this call record (extra safety check)
      const { data: { user } } = await supabase.auth.getUser();
      if (!user || callRecord.user_id !== user.id) {
        console.error("❌ Call record belongs to different user");
        throw new Error("Cannot restore recording - access denied");
      }

      // NEW: If DB indicates recording is already complete, DO NOT resume microphone
      const total = (callRecord as any).total_chunks as number | null;
      const uploaded = (callRecord as any).chunks_uploaded as number | null;
      const isCompleteFlag = (callRecord as any).recording_complete === true;
      const uploadsMatch = typeof total === 'number' && total > 0 && typeof uploaded === 'number' && uploaded >= total;
      if (isCompleteFlag || uploadsMatch) {
        console.log("ℹ️ Recording already completed in DB; skipping restore and clearing local state");
        ChunkedRecordingManager.clearState();
        this.isRecording = false;
        this.recordingComplete = true;
        this.updateProgress();
        return false;
      }

      console.log("✅ Call record verified, proceeding with restoration");

      this.callRecordId = state.callRecordId;
      this.currentChunkNumber = state.currentChunkNumber;
      this.totalStartTime = state.totalStartTime;
      this.currentSliceSeq = state.currentSliceSeq ?? 0;

      // Reconstruct completed chunks from DB so UI reflects reality
      const { data: dbChunks, error } = await supabase
        .from("call_chunks")
        .select("chunk_number,duration_seconds,file_size")
        .eq("call_record_id", state.callRecordId)
        .eq("upload_status", "uploaded")
        .order("chunk_number", { ascending: true });

      if (!error && dbChunks?.length) {
        this.chunks = dbChunks.map((dbChunk: any) => ({
          id: `${state.callRecordId}-chunk-${dbChunk.chunk_number}`,
          callRecordId: state.callRecordId,
          chunkNumber: dbChunk.chunk_number,
          audioBlob: new Blob(), // audio already in storage
          duration: dbChunk.duration_seconds || 0,
          fileSize: dbChunk.file_size || 0,
          uploadStatus: "completed",
          retryCount: 0,
        }));
        const maxDbChunk = dbChunks.reduce((max: number, c: any) => Math.max(max, c.chunk_number ?? -1), -1);
        const nextChunkNumber = Math.max(state.currentChunkNumber ?? 0, maxDbChunk + 1);
        if (nextChunkNumber !== this.currentChunkNumber) {
          this.currentChunkNumber = nextChunkNumber;
        }
        console.log(`✅ Reconstructed ${this.chunks.length} completed chunks from DB`);
      }

      // Try to rebuild unfinished chunk from IDB slices
      const partial = await this.rebuildUnfinishedChunk(state.callRecordId, this.currentChunkNumber);
      if (partial && partial.size > 0) {
        const durationGuess = state.currentChunkStartTime
          ? Math.max(1, (Date.now() - state.currentChunkStartTime) / 1000)
          : Math.max(1, partial.size / 4000);
        const chunkInfo: ChunkInfo = {
          id: `${state.callRecordId}-chunk-${this.currentChunkNumber}`,
          callRecordId: state.callRecordId,
          chunkNumber: this.currentChunkNumber,
          audioBlob: partial,
          duration: durationGuess,
          fileSize: partial.size,
          uploadStatus: "pending",
          retryCount: 0,
        };
      this.chunks.push(chunkInfo);
      const uploadSuccess = await this.uploadChunk(chunkInfo);
      // ONLY clear slices if upload succeeded - keep them for retry if failed
      if (uploadSuccess) {
        await this.clearSliceGroup(state.callRecordId, this.currentChunkNumber);
      }
      
      // NEW: Query DB to get actual highest chunk number for proper sequencing
      const { data: maxChunkData } = await supabase
        .from("call_chunks")
        .select("chunk_number")
        .eq("call_record_id", state.callRecordId)
        .order("chunk_number", { ascending: false })
        .limit(1)
        .maybeSingle();

      const actualMaxChunk = maxChunkData?.chunk_number ?? -1;
      this.currentChunkNumber = actualMaxChunk + 1;
      this.currentSliceSeq = 0;
      console.log(`📊 Synced after restore: next chunk will be ${this.currentChunkNumber}`);
      }

      // Only call resumeRecording if we don't already have an active recording
      if (!this.isRecording || !this.mediaRecorder || this.mediaRecorder.state !== "recording") {
        console.log('📞 No active recording, calling resumeRecording to rebuild');
        await this.resumeRecording();
      } else {
        console.log('✅ Recording already active, skipping resumeRecording');
        this.updateProgress();
      }
      
      return true;
    } catch (error) {
      console.error("Failed to restore recording state:", error);
      return false;
    }
  }

  /* --------------------------------- Public API -------------------------------- */

  async startRecording(callRecordId: string): Promise<void> {
    if (this.isRecording) throw new Error("Recording already in progress");

    this.callRecordId = callRecordId;
    this.currentChunkNumber = 0;
    this.currentSliceSeq = 0;
    this.chunks = [];
    this.isRecording = true;
    this.recordingComplete = false;
    this.totalStartTime = Date.now();

    this.saveState();
    this.bindLifecycleGuards();

    console.log("🎙️ Starting chunked recording for call:", callRecordId);

    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 24000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      // Live audio meter
      this.audioContext = new AudioContext();
      const source = this.audioContext.createMediaStreamSource(this.stream);
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 256;
      source.connect(this.analyser);
      const dataArray = new Uint8Array(this.analyser.frequencyBinCount);
      const updateLevel = () => {
        if (!this.isRecording || !this.analyser) return;
        this.analyser.getByteFrequencyData(dataArray);
        const average = dataArray.reduce((a, b) => a + b, 0) / dataArray.length;
        this.audioLevel = Math.min(100, (average / 255) * 100);
        this.audioLevelRaf = requestAnimationFrame(updateLevel);
      };
      this.audioLevelRaf = requestAnimationFrame(updateLevel);

      await this.startNextChunk();
      this.updateProgress();

      this.progressUpdateInterval = window.setInterval(() => {
        if (this.isRecording) this.updateProgress();
      }, 1000);
    } catch (error: any) {
      console.error("❌ Failed to start recording:", error);
      this.isRecording = false;
      if (error?.name === "NotAllowedError")
        throw new Error("Microphone access denied. Please allow access and try again.");
      if (error?.name === "NotFoundError")
        throw new Error("No microphone found. Please connect a microphone and try again.");
      if (error?.name === "NotReadableError")
        throw new Error("Microphone in use by another app. Close it and try again.");
      if (error?.name === "OverconstrainedError") throw new Error("Microphone does not support required settings.");
      throw new Error("Failed to access microphone. Check browser permissions and try again.");
    }
  }

  async pauseRecording(): Promise<void> {
    if (!this.isRecording) return;
    console.log("⏸️ Pausing recording");
    this.isRecording = false;

    if (this.progressUpdateInterval) {
      clearInterval(this.progressUpdateInterval);
      this.progressUpdateInterval = null;
    }
    if (this.audioLevelRaf) {
      cancelAnimationFrame(this.audioLevelRaf);
      this.audioLevelRaf = null;
    }
    if (this.audioContext) {
      this.audioContext.close();
      this.audioContext = null;
      this.analyser = null;
      this.audioLevel = 0;
    }
    if (this.mediaRecorder?.state === "recording") {
      try {
        this.mediaRecorder.requestData();
      } catch {}
      this.mediaRecorder.stop(); // triggers finalize of current chunk from slices
    }
    if (this.stream) {
      this.stream.getTracks().forEach((t) => t.stop());
      this.stream = null;
    }

    this.saveState();
    this.updateProgress();
  }

  async resumeRecording(): Promise<void> {
    if (this.isRecording || !this.callRecordId) return;
    this.bindLifecycleGuards();

    console.log("▶️ Resuming recording");
    this.isRecording = true;
    this.recordingComplete = false;

    // NEW: Sync chunk number with DB reality BEFORE starting
    const { supabase } = await import("@/integrations/supabase/client");
    const { data: maxChunkData } = await supabase
      .from("call_chunks")
      .select("chunk_number")
      .eq("call_record_id", this.callRecordId)
      .order("chunk_number", { ascending: false })
      .limit(1)
      .maybeSingle();

    if (maxChunkData) {
      this.currentChunkNumber = maxChunkData.chunk_number + 1;
      console.log(`📊 Synced on resume: next chunk will be ${this.currentChunkNumber}`);
    }

    // Auto-retry any failed uploads when resuming
    this.retryFailedChunks().catch(console.error);

    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 24000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      this.audioContext = new AudioContext();
      const source = this.audioContext.createMediaStreamSource(this.stream);
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 256;
      source.connect(this.analyser);
      const dataArray = new Uint8Array(this.analyser.frequencyBinCount);
      const updateLevel = () => {
        if (!this.isRecording || !this.analyser) return;
        this.analyser.getByteFrequencyData(dataArray);
        const average = dataArray.reduce((a, b) => a + b, 0) / dataArray.length;
        this.audioLevel = Math.min(100, (average / 255) * 100);
        this.audioLevelRaf = requestAnimationFrame(updateLevel);
      };
      this.audioLevelRaf = requestAnimationFrame(updateLevel);

      await this.startNextChunk();
      this.updateProgress();

      this.progressUpdateInterval = window.setInterval(() => {
        if (this.isRecording) this.updateProgress();
      }, 1000);
    } catch (error) {
      console.error("❌ Failed to resume recording:", error);
      this.isRecording = false;
      throw error;
    }
  }

  async stopRecording(): Promise<void> {
    if (!this.isRecording) {
      if (this.callRecordId) await this.updateCallRecordCompletion();
      this.updateProgress();
      return;
    }

    console.log("🛑 Stopping chunked recording");
    this.isRecording = false;
    this.recordingComplete = true;

    if (this.progressUpdateInterval) {
      clearInterval(this.progressUpdateInterval);
      this.progressUpdateInterval = null;
    }
    if (this.audioLevelRaf) {
      cancelAnimationFrame(this.audioLevelRaf);
      this.audioLevelRaf = null;
    }
    if (this.audioContext) {
      this.audioContext.close();
      this.audioContext = null;
      this.analyser = null;
      this.audioLevel = 0;
    }
    if (this.mediaRecorder?.state === "recording") {
      try {
        this.mediaRecorder.requestData();
      } catch {}
      this.mediaRecorder.stop(); // finalize
    }
    if (this.stream) {
      this.stream.getTracks().forEach((track) => track.stop());
      this.stream = null;
    }

    if (this.callRecordId) await this.updateCallRecordCompletion();

    ChunkedRecordingManager.clearState();
    this.updateProgress();
  }

  cleanup(force = false): void {
    // PHASE 5: When force=true, ALWAYS cleanup regardless of recording state
    // This ensures orphaned media streams are released
    if (this.isRecording && !force) {
      this.saveState();
      return;
    }

    console.log(`🧹 Cleanup called (force=${force}, isRecording=${this.isRecording})`);

    if (this.progressUpdateInterval) {
      clearInterval(this.progressUpdateInterval);
      this.progressUpdateInterval = null;
    }
    
    // CRITICAL: Stop media recorder first
    if (this.mediaRecorder) {
      if (this.mediaRecorder.state === "recording" || this.mediaRecorder.state === "paused") {
        try {
          this.mediaRecorder.requestData();
        } catch {}
        try {
          this.mediaRecorder.stop();
        } catch {}
      }
      this.mediaRecorder = null;
    }
    
    // CRITICAL: Stop all media stream tracks to release microphone
    if (this.stream) {
      console.log(`🎙️ Stopping ${this.stream.getTracks().length} media tracks`);
      this.stream.getTracks().forEach((t) => {
        t.stop();
        console.log(`  ✓ Stopped track: ${t.kind} (${t.label})`);
      });
      this.stream = null;
    }
    
    if (this.audioLevelRaf) {
      cancelAnimationFrame(this.audioLevelRaf);
      this.audioLevelRaf = null;
    }
    if (this.audioContext) {
      this.audioContext.close();
      this.audioContext = null;
      this.analyser = null;
      this.audioLevel = 0;
    }

    // Unbind lifecycle listeners
    for (const off of this._unsub) {
      try {
        off();
      } catch {}
    }
    this._unsub = [];
    this._lifecycleBound = false;

    this.chunks = [];
    this.isRecording = false;
    this.recordingComplete = false;

    if (force) {
      ChunkedRecordingManager.clearState();
      console.log('✅ Force cleanup completed - all streams stopped, state cleared');
    }
  }

  getProgress(): RecordingProgress {
    const completedChunksDuration = this.chunks.reduce((total, chunk) => total + chunk.duration, 0);
    const currentChunkDuration =
      this.isRecording && this.chunkStartTime > 0 ? (Date.now() - this.chunkStartTime) / 1000 : 0;
    const totalDuration = completedChunksDuration + currentChunkDuration;

    const chunksUploaded = this.chunks.filter((c) => c.uploadStatus === "completed").length;
    const chunksFailed = this.chunks.filter((c) => c.uploadStatus === "failed" && c.retryCount >= 3).length;

    return {
      currentChunk: this.currentChunkNumber,
      totalChunks: this.chunks.length + (this.isRecording ? 1 : 0),
      chunksUploaded,
      chunksFailed,
      isRecording: this.isRecording,
      isComplete: this.recordingComplete && chunksUploaded === this.chunks.length,
      totalDuration,
      audioLevel: this.audioLevel,
      errorMessage: undefined, // may be set in persistSlice on error
    };
  }

  async retryFailedChunks(): Promise<void> {
    const failed = this.chunks.filter((c) => c.uploadStatus === "failed");
    for (const chunk of failed) {
      chunk.retryCount = 0;
      await this.uploadChunk(chunk);
    }
  }

  async deleteRecording(): Promise<void> {
    if (!this.callRecordId) return;

    const { supabase } = await import("@/integrations/supabase/client");
    try {
      // Stop recording first
      await this.stopRecording();

      // Get all file paths from DB and delete those from storage
      const { data: rows, error: qErr } = await supabase
        .from("call_chunks")
        .select("file_path")
        .eq("call_record_id", this.callRecordId);
      if (qErr) throw qErr;

      if (rows?.length) {
        await supabase.storage.from("call-recordings").remove(rows.map((r) => r.file_path));
      }

      // Mark rows deleted or remove them, then delete the call record
      await supabase.from("call_chunks").update({ upload_status: "deleted" }).eq("call_record_id", this.callRecordId);
      await supabase.from("call_records").delete().eq("id", this.callRecordId);

      // Clear IndexedDB slices
      for (let i = 0; i <= this.currentChunkNumber; i++) {
        await this.clearSliceGroup(this.callRecordId, i);
      }

      // Cleanup
      this.cleanup(true);
      ChunkedRecordingManager.clearState();

      console.log("🗑️ Recording deleted successfully");
    } catch (error) {
      console.error("❌ Failed to delete recording:", error);
      throw error;
    }
  }

  /* ------------------------------ Internal bits ------------------------------ */

  private async startNextChunk(): Promise<void> {
    if (!this.stream || !this.callRecordId) return;

    this.chunkStartTime = Date.now();
    this.currentSliceSeq = 0;

    const preferred = "audio/webm;codecs=opus";
    const mimeType = (window as any).MediaRecorder?.isTypeSupported?.(preferred) ? preferred : "audio/webm";

    this.mediaRecorder = new MediaRecorder(this.stream, { mimeType });

    const chunkNo = this.currentChunkNumber;
    const chunkId = `${this.callRecordId}-chunk-${chunkNo}`;
    console.log(`🎵 Starting chunk ${chunkNo} (DB-synced, total in memory: ${this.chunks.length}):`, chunkId);

    // Capture browser-generated slices every `sliceDuration` ms
    this.mediaRecorder.ondataavailable = (event) => {
      if (event.data && event.data.size > 0) {
        this.persistSlice(this.callRecordId!, chunkNo, this.currentSliceSeq++, event.data).catch((e) => {
          console.warn("Persist slice failed", e);
          const p = this.getProgress();
          this.onProgressUpdate?.({
            ...p,
            errorMessage: "Local storage full — slices not saved. Consider freeing space.",
          });
        });
      }
    };

    this.mediaRecorder.onerror = (event) => {
      console.error("❌ MediaRecorder error:", event);
      this.updateProgress();
    };

    this.mediaRecorder.onstop = async () => {
      // Rebuild this chunk from slices and upload
      const rebuilt = await this.rebuildUnfinishedChunk(this.callRecordId!, chunkNo);
      const hasData = !!rebuilt && rebuilt.size > 0;

      if (!hasData) {
        // nothing recorded → clean and continue
        await this.clearSliceGroup(this.callRecordId!, chunkNo);
        if (this.isRecording) await this.startNextChunk();
        this.updateProgress();
        return;
      }

      const audioBlob = rebuilt!;
      const duration = Math.max(1, (Date.now() - this.chunkStartTime) / 1000);

      const chunkInfo: ChunkInfo = {
        id: chunkId,
        callRecordId: this.callRecordId!,
        chunkNumber: chunkNo,
        audioBlob,
        duration,
        fileSize: audioBlob.size,
        uploadStatus: "pending",
        retryCount: 0,
      };

      this.chunks.push(chunkInfo);
      const uploadSuccess = await this.uploadChunk(chunkInfo);
      // ONLY clear slices if upload succeeded - keep them for retry/restore if failed
      if (uploadSuccess) {
        console.log(`✅ Chunk ${chunkNo} uploaded successfully to DB`);
        await this.clearSliceGroup(this.callRecordId!, chunkNo);
      } else {
        console.log(`⚠️ Chunk ${chunkNo} upload failed, will retry`);
      }

      // Advance to next chunk if still recording
      this.currentChunkNumber++;
      console.log(`➡️ Advanced to chunk ${this.currentChunkNumber}`);
      this.saveState();

      if (this.isRecording) {
        await this.startNextChunk();
      }
      this.updateProgress();
    };

    // Begin recording with timeslice — this keeps slices flowing even if timers are throttled
    this.mediaRecorder.start(this.sliceDuration);

    // Hard stop after 5 minutes to form a server-side “chunk”
    if (this._chunkHardStopTimer) clearTimeout(this._chunkHardStopTimer);
    this._chunkHardStopTimer = window.setTimeout(() => {
      if (this.mediaRecorder?.state === "recording") {
        if (document.visibilityState === "hidden") {
          // Defer stopping while hidden; re-check shortly. Visibility handler will finalize when visible.
          if (this._chunkHardStopTimer) clearTimeout(this._chunkHardStopTimer);
          this._chunkHardStopTimer = window.setTimeout(() => {
            if (this.mediaRecorder?.state === "recording" && document.visibilityState !== "hidden") {
              try { this.mediaRecorder.requestData(); } catch {}
              this.mediaRecorder.stop();
            }
          }, 30000); // re-check in 30s while backgrounded
        } else {
          try { this.mediaRecorder.requestData(); } catch {}
          this.mediaRecorder.stop();
        }
      }
    }, this.chunkDuration);

    // Save metadata for restore
    this.saveState();
  }

  private async persistSlice(callId: string, chunkNo: number, seq: number, blob: Blob) {
    await sliceStore.putSlice(callId, chunkNo, seq, blob);
  }

  private async rebuildUnfinishedChunk(callId: string, chunkNo: number): Promise<Blob | null> {
    const slices = await sliceStore.getSlices(callId, chunkNo);
    if (!slices.length) return null;
    return new Blob(
      slices.map((s) => s.blob),
      { type: "audio/webm" },
    );
  }

  private async clearSliceGroup(callId: string, chunkNo: number) {
    try {
      await sliceStore.clearGroup(callId, chunkNo);
    } catch {}
  }

  private async uploadChunk(chunkInfo: ChunkInfo): Promise<boolean> {
    const { supabase } = await import("@/integrations/supabase/client");

    chunkInfo.uploadStatus = "uploading";
    this.updateProgress();

    // If offline, defer upload until connection restores
    if (typeof navigator !== "undefined" && "onLine" in navigator && (navigator as any).onLine === false) {
      console.warn(`⚠️ Offline - deferring upload for chunk ${chunkInfo.chunkNumber}`);
      chunkInfo.uploadStatus = "pending";
      window.addEventListener("online", () => this.uploadChunk(chunkInfo), { once: true });
      this.updateProgress();
      return false;
    }

    try {
      // Get authenticated user for RLS-compliant path
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error('Not authenticated - cannot upload chunk');
      
      console.log(`📤 Uploading chunk ${chunkInfo.chunkNumber} for user ${user.id}`);
      const fileName = `${user.id}/${chunkInfo.callRecordId}/chunk-${chunkInfo.chunkNumber}.webm`;

      const { data: uploadData, error: uploadError } = await supabase.storage
        .from("call-recordings")
        .upload(fileName, chunkInfo.audioBlob, { contentType: "audio/webm", upsert: true });

      if (uploadError && (uploadError as any).status !== 409 && (uploadError as any).statusCode !== "409") {
        throw uploadError;
      }
      const storagePath = uploadData?.path || fileName;

      const { error: dbError } = await supabase.from("call_chunks").insert({
        call_record_id: chunkInfo.callRecordId,
        chunk_number: chunkInfo.chunkNumber,
        file_path: storagePath,
        duration_seconds: chunkInfo.duration,
        file_size: chunkInfo.fileSize,
        upload_status: "uploaded",
        uploaded_at: new Date().toISOString(),
      });

      // Treat duplicate key (same chunk_number inserted already) as success
      if (dbError && (dbError as any).code !== '23505') throw dbError;

      chunkInfo.uploadStatus = "completed";
      console.log(`✅ Chunk ${chunkInfo.chunkNumber} uploaded to storage and recorded in DB at ${new Date().toISOString()}`);
      console.log(`   Storage path: ${storagePath}`);
      console.log(`   Duration: ${chunkInfo.duration}s, Size: ${chunkInfo.fileSize} bytes`);
      
      // Sync chunk count in real-time after successful upload
      await this.syncChunkCount();
      
      this.updateProgress();
      return true; // SUCCESS - caller can now safely delete slices
    } catch (error) {
      console.error(`❌ Failed to upload chunk ${chunkInfo.chunkNumber}:`, error);
      
      // Surface RLS violations immediately
      const errorMessage = (error as any)?.message || '';
      const statusCode = (error as any)?.statusCode || (error as any)?.status;
      if (errorMessage.includes('row-level security') || statusCode === '403' || statusCode === 403) {
        console.error('🚫 RLS violation - storage policy blocking upload');
        this.onProgressUpdate?.({ 
          ...this.getProgress(), 
          errorMessage: 'Upload blocked by security policy. Please contact support.' 
        });
      }

      // If tab is hidden or offline, defer and don't burn retries
      const isHidden = typeof document !== "undefined" && document.visibilityState === "hidden";
      const isOffline = typeof navigator !== "undefined" && "onLine" in navigator && (navigator as any).onLine === false;
      if (isHidden || isOffline) {
        chunkInfo.uploadStatus = "pending";
        this.updateProgress();

        if (isHidden) {
          const visHandler = () => {
            if (document.visibilityState === "visible") {
              document.removeEventListener("visibilitychange", visHandler);
              this.uploadChunk(chunkInfo);
            }
          };
          document.addEventListener("visibilitychange", visHandler);
        }
        if (isOffline) {
          window.addEventListener("online", () => this.uploadChunk(chunkInfo), { once: true });
        }
        return false;
      }

      // Backoff retry for transient errors
      chunkInfo.uploadStatus = "failed";
      chunkInfo.retryCount++;
      this.updateProgress();
      if (chunkInfo.retryCount < 5) {
        const delay = Math.min(30000, 5000 * Math.pow(2, chunkInfo.retryCount - 1));
        setTimeout(() => this.uploadChunk(chunkInfo), delay);
      }
      
      return false; // FAILURE - caller must keep slices for later retry/restore
    }
  }

  private async syncChunkCount(): Promise<void> {
    if (!this.callRecordId) return;
    const { supabase } = await import("@/integrations/supabase/client");
    try {
      const { count, error: countError } = await supabase
        .from("call_chunks")
        .select("id", { count: "exact", head: true })
        .eq("call_record_id", this.callRecordId)
        .eq("upload_status", "uploaded");
      
      if (countError) throw countError;
      
      const actualChunkCount = typeof count === "number" ? count : 0;
      const inMemoryCount = this.chunks.length;
      console.log(`📊 Sync chunk count: DB=${actualChunkCount}, Memory=${inMemoryCount}`);
      
      const { error } = await supabase
        .from("call_records")
        .update({ total_chunks: actualChunkCount })
        .eq("id", this.callRecordId);
        
      if (error) throw error;
    } catch (error) {
      console.error("❌ Failed to sync chunk count:", error);
    }
  }

  private async updateCallRecordCompletion(): Promise<void> {
    if (!this.callRecordId) return;
    const { supabase } = await import("@/integrations/supabase/client");
    try {
      // Query actual uploaded chunks from DB, not in-memory array
      const { count, error: countError } = await supabase
        .from("call_chunks")
        .select("id", { count: "exact", head: true })
        .eq("call_record_id", this.callRecordId)
        .eq("upload_status", "uploaded");
      
      if (countError) throw countError;
      
      const actualChunkCount = typeof count === "number" ? count : 0;
      const inMemoryCount = this.chunks.length;
      console.log(`📊 Marking recording complete:`);
      console.log(`   Actual uploaded chunks in DB: ${actualChunkCount}`);
      console.log(`   In-memory chunks: ${inMemoryCount}`);
      console.log(`   Recording complete timestamp: ${new Date().toISOString()}`);
      
      const { error } = await supabase
        .from("call_records")
        .update({
          total_chunks: actualChunkCount,
          recording_complete: true,
        })
        .eq("id", this.callRecordId);
      if (error) throw error;
      console.log("✅ Call record marked as complete");
    } catch (error) {
      console.error("❌ Failed to update call record:", error);
    }
  }

  private updateProgress(): void {
    if (!this.onProgressUpdate) return;

    const completedChunksDuration = this.chunks.reduce((total, chunk) => total + chunk.duration, 0);
    const currentChunkDuration =
      this.isRecording && this.chunkStartTime > 0 ? (Date.now() - this.chunkStartTime) / 1000 : 0;
    const totalDuration = completedChunksDuration + currentChunkDuration;

    const chunksUploaded = this.chunks.filter((c) => c.uploadStatus === "completed").length;
    const chunksFailed = this.chunks.filter((c) => c.uploadStatus === "failed" && c.retryCount >= 5).length;

    const progress: RecordingProgress = {
      currentChunk: this.currentChunkNumber,
      totalChunks: this.chunks.length + (this.isRecording ? 1 : 0),
      chunksUploaded,
      chunksFailed,
      isRecording: this.isRecording,
      isComplete: this.recordingComplete && chunksUploaded === this.chunks.length,
      totalDuration,
      audioLevel: this.audioLevel,
      errorMessage: undefined,
    };

    this.onProgressUpdate(progress);
  }
}

/* ------------------------------ Utils (export) ------------------------------ */

export const formatDuration = (seconds: number): string => {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainingSeconds = Math.floor(seconds % 60);
  if (hours > 0)
    return `${hours}:${minutes.toString().padStart(2, "0")}:${remainingSeconds.toString().padStart(2, "0")}`;
  return `${minutes}:${remainingSeconds.toString().padStart(2, "0")}`;
};
