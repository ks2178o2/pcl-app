// Basic Tabs components for testing
import React from 'react';

export const Tabs = ({ children, defaultValue, value, onValueChange, ...props }: any) => (
  <div className="tabs" {...props}>{children}</div>
);

export const TabsContent = ({ children, value, className = '', ...props }: any) => (
  <div className={`tabs-content ${className}`} {...props}>{children}</div>
);

export const TabsList = ({ children, className = '', ...props }: any) => (
  <div className={`tabs-list ${className}`} {...props}>{children}</div>
);

export const TabsTrigger = ({ children, value, className = '', ...props }: any) => (
  <button className={`tabs-trigger ${className}`} {...props}>{children}</button>
);
