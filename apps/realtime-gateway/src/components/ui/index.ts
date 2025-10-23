// Basic UI components for testing
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

export const Input = ({ className = '', ...props }: any) => (
  <input className={`input ${className}`} {...props} />
);

export const Label = ({ children, className = '', ...props }: any) => (
  <label className={`label ${className}`} {...props}>{children}</label>
);

export const Textarea = ({ className = '', ...props }: any) => (
  <textarea className={`textarea ${className}`} {...props} />
);

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

export const Table = ({ children, className = '', ...props }: any) => (
  <table className={`table ${className}`} {...props}>{children}</table>
);

export const TableBody = ({ children, className = '', ...props }: any) => (
  <tbody className={`table-body ${className}`} {...props}>{children}</tbody>
);

export const TableCell = ({ children, className = '', ...props }: any) => (
  <td className={`table-cell ${className}`} {...props}>{children}</td>
);

export const TableHead = ({ children, className = '', ...props }: any) => (
  <th className={`table-head ${className}`} {...props}>{children}</th>
);

export const TableHeader = ({ children, className = '', ...props }: any) => (
  <thead className={`table-header ${className}`} {...props}>{children}</thead>
);

export const TableRow = ({ children, className = '', ...props }: any) => (
  <tr className={`table-row ${className}`} {...props}>{children}</tr>
);

export const Progress = ({ value = 0, className = '', ...props }: any) => (
  <div className={`progress ${className}`} {...props}>
    <div className="progress-bar" style={{ width: `${value}%` }} />
  </div>
);
