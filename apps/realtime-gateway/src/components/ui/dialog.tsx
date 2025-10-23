// Basic Dialog components for testing
import React from 'react';

export const Dialog = ({ children, ...props }: any) => (
  <div className="dialog" {...props}>{children}</div>
);

export const DialogContent = ({ children, className = '', ...props }: any) => (
  <div className={`dialog-content ${className}`} {...props}>{children}</div>
);

export const DialogDescription = ({ children, className = '', ...props }: any) => (
  <div className={`dialog-description ${className}`} {...props}>{children}</div>
);

export const DialogHeader = ({ children, className = '', ...props }: any) => (
  <div className={`dialog-header ${className}`} {...props}>{children}</div>
);

export const DialogTitle = ({ children, className = '', ...props }: any) => (
  <h2 className={`dialog-title ${className}`} {...props}>{children}</h2>
);

export const DialogTrigger = ({ children, ...props }: any) => (
  <div {...props}>{children}</div>
);
