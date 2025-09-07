'use client';

import { ReactNode } from 'react';
import styles from './Modal.module.css';

interface ModalOverlayProps {
  children: ReactNode;
  size?: 'small' | 'medium' | 'large' | 'fullscreen';
  closable?: boolean;
  backdrop?: boolean;
  onClose?: () => void;
}

export default function ModalOverlay({ 
  children, 
  size = 'medium', 
  closable = true, 
  backdrop = true,
  onClose 
}: ModalOverlayProps) {
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget && closable && onClose) {
      onClose();
    }
  };

  const handleCloseClick = () => {
    if (closable && onClose) {
      onClose();
    }
  };

  return (
    <div 
      className={`${styles.overlay} ${!backdrop ? styles.noBackdrop : ''}`}
      onClick={handleBackdropClick}
    >
      <div className={`${styles.modal} ${styles[size]}`}>
        {closable && (
          <button 
            className={styles.closeButton}
            onClick={handleCloseClick}
            aria-label="Close modal"
          >
            ×
          </button>
        )}
        {children}
      </div>
    </div>
  );
}