// Basic Progress component for testing
import React from 'react';

export const Progress = ({ value = 0, className = '', ...props }: any) => (
  <div className={`progress ${className}`} {...props}>
    <div className="progress-bar" style={{ width: `${value}%` }} />
  </div>
);
