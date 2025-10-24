import React, { useState } from 'react';
import { RecordingStateContext } from '@/hooks/useRecordingState';

interface RecordingStateProviderProps {
  children: React.ReactNode;
}

export const RecordingStateProvider: React.FC<RecordingStateProviderProps> = ({ children }) => {
  const [isRecording, setIsRecording] = useState(false);

  return (
    <RecordingStateContext.Provider value={{ isRecording, setIsRecording }}>
      {children}
    </RecordingStateContext.Provider>
  );
};