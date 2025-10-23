// Basic Textarea component for testing
import React from 'react';

export const Textarea = ({ className = '', ...props }: any) => (
  <textarea className={`textarea ${className}`} {...props} />
);
