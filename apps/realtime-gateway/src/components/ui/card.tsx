// Basic Card components for testing
import React from 'react';

export const Card = ({ children, className = '', ...props }: any) => (
  <div className={`card ${className}`} {...props}>{children}</div>
);

export const CardContent = ({ children, className = '', ...props }: any) => (
  <div className={`card-content ${className}`} {...props}>{children}</div>
);

export const CardDescription = ({ children, className = '', ...props }: any) => (
  <div className={`card-description ${className}`} {...props}>{children}</div>
);

export const CardHeader = ({ children, className = '', ...props }: any) => (
  <div className={`card-header ${className}`} {...props}>{children}</div>
);

export const CardTitle = ({ children, className = '', ...props }: any) => (
  <h3 className={`card-title ${className}`} {...props}>{children}</h3>
);
