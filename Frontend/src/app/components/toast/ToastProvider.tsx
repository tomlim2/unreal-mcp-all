'use client';

import { createContext, useContext, useState, useCallback, ReactNode, useRef } from 'react';
import { ToastContextType, ToastState, BaseToastConfig, ToastPosition } from './types';
import ToastContainer from './ToastContainer';

// Create the toast context
const ToastContext = createContext<ToastContextType | null>(null);

// Custom hook to use toast context
export const useToastContext = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToastContext must be used within a ToastProvider');
  }
  return context;
};

// Toast Provider Props
interface ToastProviderProps {
  children: ReactNode;
  position?: ToastPosition;
  maxToasts?: number;
}

// Generate unique ID for toasts
const generateId = () => `toast_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

export default function ToastProvider({ 
  children, 
  position = 'top-right',
  maxToasts = 5 
}: ToastProviderProps) {
  const [toasts, setToasts] = useState<ToastState[]>([]);
  const [toastPosition, setToastPosition] = useState<ToastPosition>(position);
  const timeoutsRef = useRef<Map<string, NodeJS.Timeout>>(new Map());

  // Clean up timeouts when component unmounts
  const cleanupTimeout = useCallback((id: string) => {
    const timeout = timeoutsRef.current.get(id);
    if (timeout) {
      clearTimeout(timeout);
      timeoutsRef.current.delete(id);
    }
  }, []);

  // Dismiss toast
  const dismissToast = useCallback((id: string) => {
    setToasts(prev => {
      const toast = prev.find(t => t.id === id);
      if (toast && toast.onDismiss) {
        toast.onDismiss();
      }
      
      // Mark as exiting first for animation
      const updated = prev.map(t => 
        t.id === id ? { ...t, isExiting: true } : t
      );
      
      // Remove after animation
      setTimeout(() => {
        setToasts(current => current.filter(t => t.id !== id));
        cleanupTimeout(id);
      }, 300); // Match animation duration
      
      return updated;
    });
  }, [cleanupTimeout]);

  // Dismiss all toasts
  const dismissAll = useCallback(() => {
    setToasts(prev => prev.map(t => ({ ...t, isExiting: true })));
    
    setTimeout(() => {
      setToasts([]);
      timeoutsRef.current.forEach(timeout => clearTimeout(timeout));
      timeoutsRef.current.clear();
    }, 300);
  }, []);

  // Show toast
  const showToast = useCallback((config: Omit<BaseToastConfig, 'id'>): string => {
    const id = generateId();
    const duration = config.duration !== undefined ? config.duration : 4000; // 4 seconds default
    
    const toastState: ToastState = {
      ...config,
      id,
      createdAt: Date.now(),
      isVisible: true,
      isExiting: false,
      dismissible: config.dismissible !== false // default true
    };

    setToasts(prev => {
      let newToasts = [...prev, toastState];
      
      // Remove oldest toasts if exceeding maxToasts
      if (newToasts.length > maxToasts) {
        const toRemove = newToasts.slice(0, newToasts.length - maxToasts);
        toRemove.forEach(toast => {
          cleanupTimeout(toast.id);
        });
        newToasts = newToasts.slice(-maxToasts);
      }
      
      return newToasts;
    });

    // Auto-dismiss after duration (if not persistent)
    if (duration > 0) {
      const timeout = setTimeout(() => {
        dismissToast(id);
      }, duration);
      timeoutsRef.current.set(id, timeout);
    }

    return id;
  }, [maxToasts, cleanupTimeout, dismissToast]);

  // Convenience methods
  const showSuccess = useCallback((message: string, options?: Partial<BaseToastConfig>): string => {
    return showToast({ type: 'success', message, ...options });
  }, [showToast]);

  const showError = useCallback((message: string, options?: Partial<BaseToastConfig>): string => {
    return showToast({ type: 'error', message, duration: 0, ...options }); // Errors persist by default
  }, [showToast]);

  const showWarning = useCallback((message: string, options?: Partial<BaseToastConfig>): string => {
    return showToast({ type: 'warning', message, ...options });
  }, [showToast]);

  const showInfo = useCallback((message: string, options?: Partial<BaseToastConfig>): string => {
    return showToast({ type: 'info', message, ...options });
  }, [showToast]);

  const contextValue: ToastContextType = {
    toasts,
    position: toastPosition,
    setPosition: setToastPosition,
    showToast,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    dismissToast,
    dismissAll
  };

  return (
    <ToastContext.Provider value={contextValue}>
      {children}
      <ToastContainer 
        toasts={toasts} 
        position={toastPosition}
        onDismiss={dismissToast}
      />
    </ToastContext.Provider>
  );
}