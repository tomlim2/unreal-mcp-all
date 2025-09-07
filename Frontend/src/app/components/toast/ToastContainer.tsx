'use client';

import { createPortal } from 'react-dom';
import { useEffect, useState } from 'react';
import { ToastState, ToastPosition } from './types';
import Toast from './Toast';
import styles from './Toast.module.css';

interface ToastContainerProps {
  toasts: ToastState[];
  position: ToastPosition;
  onDismiss: (id: string) => void;
}

export default function ToastContainer({ toasts, position, onDismiss }: ToastContainerProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted || typeof window === 'undefined') {
    return null;
  }

  const getPositionClass = () => {
    switch (position) {
      case 'top-left': return styles.topLeft;
      case 'top-center': return styles.topCenter;
      case 'top-right': return styles.topRight;
      case 'bottom-left': return styles.bottomLeft;
      case 'bottom-center': return styles.bottomCenter;
      case 'bottom-right': return styles.bottomRight;
      default: return styles.topRight;
    }
  };

  return createPortal(
    <div className={`${styles.toastContainer} ${getPositionClass()}`}>
      {toasts.map(toast => (
        <Toast 
          key={toast.id}
          toast={toast}
          onDismiss={onDismiss}
        />
      ))}
    </div>,
    document.body
  );
}