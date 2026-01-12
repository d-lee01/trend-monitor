/**
 * Toast notification system using React Context
 * Provides global toast state management for success/error/warning messages
 */

import { createContext, useContext } from 'react';

export type ToastType = 'success' | 'error' | 'warning';

export interface ToastMessage {
  id: string;
  type: ToastType;
  message: string;
  duration?: number; // milliseconds
}

export interface ToastContextType {
  toasts: ToastMessage[];
  showToast: (options: Omit<ToastMessage, 'id'>) => void;
  removeToast: (id: string) => void;
}

export const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}
