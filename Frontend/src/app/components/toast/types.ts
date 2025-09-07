import { ReactNode } from 'react';

// Toast types
export type ToastType = 'success' | 'error' | 'warning' | 'info';

// Toast positions
export type ToastPosition = 
  | 'top-left' 
  | 'top-center' 
  | 'top-right'
  | 'bottom-left'
  | 'bottom-center'
  | 'bottom-right';

// Base toast configuration
export interface BaseToastConfig {
  id?: string;
  type: ToastType;
  title?: string;
  message: string;
  duration?: number; // milliseconds, 0 for persistent
  dismissible?: boolean;
  action?: {
    label: string;
    onClick: () => void;
  };
  onDismiss?: () => void;
}

// Toast state
export interface ToastState extends BaseToastConfig {
  id: string;
  createdAt: number;
  isVisible: boolean;
  isExiting: boolean;
}

// Toast context types
export interface ToastContextType {
  toasts: ToastState[];
  position: ToastPosition;
  setPosition: (position: ToastPosition) => void;
  
  // Toast operations
  showToast: (config: Omit<BaseToastConfig, 'id'>) => string;
  showSuccess: (message: string, options?: Partial<BaseToastConfig>) => string;
  showError: (message: string, options?: Partial<BaseToastConfig>) => string;
  showWarning: (message: string, options?: Partial<BaseToastConfig>) => string;
  showInfo: (message: string, options?: Partial<BaseToastConfig>) => string;
  
  dismissToast: (id: string) => void;
  dismissAll: () => void;
}

// Hook return type
export type UseToastReturn = Omit<ToastContextType, 'toasts' | 'position' | 'setPosition'>;