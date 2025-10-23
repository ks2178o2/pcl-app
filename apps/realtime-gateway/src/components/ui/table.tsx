// Basic Table components for testing
import React from 'react';

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
