// Basic Select components for testing
import React from 'react';

export const Select = ({ children, ...props }: any) => (
  <select {...props}>{children}</select>
);

export const SelectContent = ({ children, ...props }: any) => (
  <div {...props}>{children}</div>
);

export const SelectItem = ({ children, value, ...props }: any) => (
  <option value={value} {...props}>{children}</option>
);

export const SelectTrigger = ({ children, className = '', ...props }: any) => (
  <div className={`select-trigger ${className}`} {...props}>{children}</div>
);

export const SelectValue = ({ placeholder, ...props }: any) => (
  <span {...props}>{placeholder}</span>
);
