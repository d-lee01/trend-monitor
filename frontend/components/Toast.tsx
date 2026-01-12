'use client';

import { useState, useEffect, useCallback, useRef, ReactNode } from 'react';
import { ToastContext, ToastMessage, ToastType } from '@/lib/toast';

interface ToastProviderProps {
  children: ReactNode;
}

export function ToastProvider({ children }: ToastProviderProps) {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const timeoutsRef = useRef<Map<string, NodeJS.Timeout>>(new Map());

  const removeToast = useCallback((id: string) => {
    // Clear timeout if it exists
    const timeoutId = timeoutsRef.current.get(id);
    if (timeoutId) {
      clearTimeout(timeoutId);
      timeoutsRef.current.delete(id);
    }
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  }, []);

  const showToast = useCallback((options: Omit<ToastMessage, 'id'>) => {
    const id = Math.random().toString(36).substring(7);
    const toast: ToastMessage = {
      id,
      type: options.type,
      message: options.message,
      duration: options.duration || 5000, // Default 5 seconds
    };

    setToasts((prev) => [...prev, toast]);

    // Auto-dismiss after duration
    const timeoutId = setTimeout(() => {
      removeToast(id);
    }, toast.duration);
    timeoutsRef.current.set(id, timeoutId);
  }, [removeToast]);

  return (
    <ToastContext.Provider value={{ toasts, showToast, removeToast }}>
      {children}
      <ToastContainer toasts={toasts} onClose={removeToast} />
    </ToastContext.Provider>
  );
}

interface ToastContainerProps {
  toasts: ToastMessage[];
  onClose: (id: string) => void;
}

function ToastContainer({ toasts, onClose }: ToastContainerProps) {
  if (toasts.length === 0) return null;

  return (
    <div
      className="fixed top-4 right-4 z-50 space-y-2"
      aria-live="polite"
      aria-atomic="true"
    >
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onClose={onClose} />
      ))}
    </div>
  );
}

interface ToastItemProps {
  toast: ToastMessage;
  onClose: (id: string) => void;
}

function ToastItem({ toast, onClose }: ToastItemProps) {
  const [isExiting, setIsExiting] = useState(false);

  const handleClose = () => {
    setIsExiting(true);
    setTimeout(() => {
      onClose(toast.id);
    }, 300); // Match animation duration
  };

  // Icon based on toast type
  const getIcon = () => {
    switch (toast.type) {
      case 'success':
        return '✓';
      case 'error':
      case 'warning':
        return '⚠';
      default:
        return '';
    }
  };

  // Colors based on toast type
  const getColorClasses = () => {
    switch (toast.type) {
      case 'success':
        return 'bg-green-50 border-green-300 text-green-800';
      case 'error':
        return 'bg-red-50 border-red-300 text-red-800';
      case 'warning':
        return 'bg-yellow-50 border-yellow-300 text-yellow-800';
      default:
        return 'bg-gray-50 border-gray-300 text-gray-800';
    }
  };

  return (
    <div
      className={`
        flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg border
        transition-all duration-300 min-w-[300px] max-w-[500px]
        ${getColorClasses()}
        ${isExiting ? 'opacity-0 translate-x-4' : 'opacity-100 translate-x-0'}
      `}
      role="alert"
    >
      <span className="text-xl" aria-hidden="true">
        {getIcon()}
      </span>
      <p className="flex-1 text-sm font-medium">
        {toast.message}
      </p>
      <button
        type="button"
        onClick={handleClose}
        className="text-gray-400 hover:text-gray-600 transition-colors"
        aria-label="Close notification"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  );
}
