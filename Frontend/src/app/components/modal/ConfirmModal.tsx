'use client';

import { ConfirmModalConfig } from './types';
import styles from './Modal.module.css';

interface ConfirmModalProps {
  config: ConfirmModalConfig;
}

export default function ConfirmModal({ config }: ConfirmModalProps) {
  return (
    <div className={styles.modalContent}>
      <div className={styles.confirmHeader}>
        <h2 className={styles.confirmTitle}>{config.title}</h2>
      </div>
      
      <div className={styles.confirmBody}>
        <p className={styles.confirmMessage}>{config.message}</p>
      </div>
      
      <div className={styles.modalFooter}>
        <button 
          className={`${styles.button} ${styles.secondaryButton}`}
          onClick={config.onCancel}
        >
          {config.cancelText || 'Cancel'}
        </button>
        <button 
          className={`${styles.button} ${styles.primaryButton} ${
            config.variant === 'danger' ? styles.dangerButton : ''
          }`}
          onClick={config.onConfirm}
        >
          {config.confirmText || 'Confirm'}
        </button>
      </div>
    </div>
  );
}