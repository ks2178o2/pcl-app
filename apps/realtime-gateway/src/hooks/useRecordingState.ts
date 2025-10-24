import { createContext, useContext, useState } from 'react';

interface RecordingStateContextType {
  isRecording: boolean;
  setIsRecording: (recording: boolean) => void;
}

const RecordingStateContext = createContext<RecordingStateContextType | undefined>(undefined);

export const useRecordingState = () => {
  const context = useContext(RecordingStateContext);
  if (!context) {
    // Return a fallback state if no provider is found
    return {
      isRecording: false,
      setIsRecording: () => {},
    };
  }
  return context;
};

export { RecordingStateContext };