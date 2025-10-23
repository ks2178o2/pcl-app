// Basic Input component for testing
import React from 'react';

export const Input = ({ className = '', ...props }: any) => (
  <input className={`input ${className}`} {...props} />
);
