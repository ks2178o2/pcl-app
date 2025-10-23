// Basic Label component for testing
import React from 'react';

export const Label = ({ children, className = '', ...props }: any) => (
  <label className={`label ${className}`} {...props}>{children}</label>
);
