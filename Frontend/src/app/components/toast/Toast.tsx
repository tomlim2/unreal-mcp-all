'use client';

import { useEffect, useState } from 'react';
import { ToastState } from './types';
import styles from './Toast.module.css';

interface ToastProps {
  toast: ToastState;
  onDismiss: (id: string) => void;
}

export default function Toast({ toast, onDismiss }: ToastProps) {
  const [progress, setProgress] = useState(100);

  // Progress bar animation for auto-dismiss toasts
  useEffect(() => {
    if (toast.duration && toast.duration > 0 && !toast.isExiting) {
      const startTime = Date.now();
      const interval = setInterval(() => {
        const elapsed = Date.now() - startTime;
        const remaining = Math.max(0, toast.duration! - elapsed);
        const progressPercent = (remaining / toast.duration!) * 100;
        
        setProgress(progressPercent);
        
        if (remaining <= 0) {
          clearInterval(interval);
        }
      }, 50);
      
      return () => clearInterval(interval);
    }
  }, [toast.duration, toast.isExiting]);

  const getIconForType = () => {
    switch (toast.type) {
      case 'success': return '✓';
      case 'error': return '✕';
      case 'warning': return '⚠';
      case 'info': return 'ℹ';
      default: return 'ℹ';
    }
  };

  const handleDismiss = () => {
    if (toast.dismissible !== false) {
      onDismiss(toast.id);
    }
  };

  const handleActionClick = () => {
    if (toast.action) {
      toast.action.onClick();
      // Optionally dismiss after action
      onDismiss(toast.id);
    }
  };

  return (
    <div 
      className={`${styles.toast} ${styles[toast.type]} ${
        toast.isExiting ? styles.exiting : styles.entering
      }`}
      role="alert"
      aria-live="polite"
    >
      <div className={styles.toastContent}>
        <div className={styles.toastIcon}>
          {getIconForType()}
        </div>
        
        <div className={styles.toastBody}>
          {toast.title && (
            <div className={styles.toastTitle}>{toast.title}</div>
          )}
          <div className={styles.toastMessage}>{toast.message}</div>
          
          {toast.action && (
            <button 
              className={styles.toastAction}
              onClick={handleActionClick}
            >
              {toast.action.label}
            </button>
          )}
        </div>
        
        {toast.dismissible !== false && (
          <button 
            className={styles.toastClose}
            onClick={handleDismiss}
            aria-label="Dismiss notification"
          >
            ×
          </button>
        )}
      </div>
      
      {/* Progress bar for auto-dismiss toasts */}
      {toast.duration && toast.duration > 0 && !toast.isExiting && (
        <div className={styles.toastProgress}>
          <div 
            className={styles.toastProgressBar}
            style={{ width: `${progress}%` }}
          />
        </div>
      )}
    </div>
  );
}