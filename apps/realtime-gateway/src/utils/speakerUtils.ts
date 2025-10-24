// Utility functions for speaker diarization and mapping

export interface DiarizationSegment {
  id: string;
  speaker: string;
  text: string;
  startTime: number;
  endTime: number;
  confidence?: number;
}

/**
 * Expand compact diarization format to standard format
 * Compact: { sp, t, s, e, c }
 * Standard: { id, speaker, text, startTime, endTime, confidence }
 */
export const expandDiarizationSegments = (
  compactSegments: any[]
): DiarizationSegment[] => {
  if (!compactSegments || compactSegments.length === 0) return [];
  
  return compactSegments.map((seg, index) => ({
    id: seg.id || `segment-${index}`,
    speaker: seg.sp || seg.speaker || 'speaker_0',
    text: seg.t || seg.text || '',
    startTime: seg.s !== undefined ? seg.s : (seg.start || 0),
    endTime: seg.e !== undefined ? seg.e : (seg.end || 0),
    confidence: seg.c !== undefined ? seg.c : (seg.confidence || 0.85)
  }));
};

/**
 * Normalize diarization segments of various shapes to standard format
 */
export const normalizeDiarizationSegments = (segments: any[]): DiarizationSegment[] => {
  if (!segments || segments.length === 0) return [];

  return segments.map((seg, index) => {
    const id = seg.id ?? `segment-${index}`;

    const speakerRaw = seg.sp ?? seg.speaker ?? seg.spk ?? seg.speaker_id ?? seg.channel ?? seg.spk_id ?? 0;
    const speaker = (typeof speakerRaw === 'number' || /^\d+$/.test(String(speakerRaw)))
      ? `speaker_${speakerRaw}`
      : String(speakerRaw || 'speaker_0');

    const start = seg.s ?? seg.start ?? seg.start_time ?? seg.ts ?? seg.offset ?? 0;
    const endCandidate = seg.e ?? seg.end ?? seg.end_time ?? seg.te ?? (start + (seg.duration ?? seg.dur ?? 0));

    const text = seg.t ?? seg.text ?? seg.word ?? seg.w ?? '';
    const confidence = seg.c ?? seg.confidence ?? seg.p ?? seg.score ?? 0.85;

    const startNum = Number(start) || 0;
    const endNum = Number(endCandidate ?? startNum) || startNum;

    return {
      id,
      speaker,
      text: String(text || ''),
      startTime: startNum,
      endTime: endNum,
      confidence: Number(confidence) || 0.85,
    } as DiarizationSegment;
  });
};

/**
 * Apply speaker mapping to transcript segments
 * Handles both compact and standard formats
 */
export const applyingSpeakerMapping = (
  segments: any[],
  speakerMapping: Record<string, string>
): DiarizationSegment[] => {
  const normalized = normalizeDiarizationSegments(segments);
  
  return normalized.map(segment => ({
    ...segment,
    speaker: speakerMapping[segment.speaker] || (
      typeof segment.speaker === 'string'
        ? segment.speaker.replace(/^speaker_/, 'Speaker ')
        : `Speaker ${segment.speaker}`
    )
  }));
};

/**
 * Generate formatted transcript from segments with applied mapping
 * Handles both compact and standard formats
 */
export const generateMappedTranscript = (
  segments: any[],
  speakerMapping: Record<string, string>
): string => {
  const mappedSegments = applyingSpeakerMapping(segments, speakerMapping);
  
  return mappedSegments
    .sort((a, b) => a.startTime - b.startTime)
    .map(segment => `[${segment.speaker}]: ${segment.text}`)
    .join('\n\n');
};

/**
 * Create default speaker mapping for two-speaker scenario
 * Handles both compact and standard formats
 */
export const createDefaultMapping = (
  segments: any[],
  salespersonName: string,
  customerName: string
): Record<string, string> => {
  // Normalize any input shape (compact, standard, vendor)
  const expandedSegments = normalizeDiarizationSegments(segments);
    
  const uniqueSpeakers = Array.from(new Set(expandedSegments.map(s => s.speaker))).sort();
  
  const mapping: Record<string, string> = {};
  
  if (uniqueSpeakers.length >= 1) {
    mapping[uniqueSpeakers[0]] = salespersonName;
  }
  if (uniqueSpeakers.length >= 2) {
    mapping[uniqueSpeakers[1]] = customerName;
  }
  
  // Handle additional speakers
  uniqueSpeakers.slice(2).forEach((speaker, index) => {
    mapping[speaker] = `Speaker ${speaker}`;
  });
  
  return mapping;
};

/**
 * Swap two speakers in the mapping
 */
export const swapSpeakers = (
  mapping: Record<string, string>,
  speaker1: string,
  speaker2: string
): Record<string, string> => {
  const newMapping = { ...mapping };
  const temp = newMapping[speaker1];
  newMapping[speaker1] = newMapping[speaker2];
  newMapping[speaker2] = temp;
  return newMapping;
};

/**
 * Calculate speaker statistics
 * Handles both compact and standard formats
 */
export const calculateSpeakerStats = (segments: any[]) => {
  // Normalize any input shape
  const expandedSegments = normalizeDiarizationSegments(segments);
    
  const speakerStats = new Map<string, {
    segmentCount: number;
    totalDuration: number;
    totalWords: number;
    avgConfidence: number;
  }>();

  expandedSegments.forEach(segment => {
    const speaker = segment.speaker;
    const duration = segment.endTime - segment.startTime;
    const wordCount = segment.text.split(/\s+/).length;
    const confidence = segment.confidence || 0.85;

    if (!speakerStats.has(speaker)) {
      speakerStats.set(speaker, {
        segmentCount: 0,
        totalDuration: 0,
        totalWords: 0,
        avgConfidence: 0
      });
    }

    const stats = speakerStats.get(speaker)!;
    stats.segmentCount++;
    stats.totalDuration += duration;
    stats.totalWords += wordCount;
    stats.avgConfidence = (stats.avgConfidence * (stats.segmentCount - 1) + confidence) / stats.segmentCount;
  });

  return speakerStats;
};