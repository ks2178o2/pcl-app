// Basic Button component for testing
import React from 'react';

export const Button = ({ children, onClick, className = '', disabled = false, ...props }: any) => (
  <button 
    className={`btn ${className}`} 
    onClick={onClick} 
    disabled={disabled}
    {...props}
  >
    {children}
  </button>
);
