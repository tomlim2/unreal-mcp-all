'use client';

import { useEffect } from 'react';
import { AlertModalConfig } from './types';
import styles from './Modal.module.css';

interface AlertModalProps {
  config: AlertModalConfig;
}

export default function AlertModal({ config }: AlertModalProps) {
  useEffect(() => {
    if (config.autoClose && config.onClose) {
      const timer = setTimeout(config.onClose, config.autoClose);
      return () => clearTimeout(timer);
    }
  }, [config.autoClose, config.onClose]);

  const handleConfirm = () => {
    if (config.onConfirm) {
      config.onConfirm();
    }
    if (config.onClose) {
      config.onClose();
    }
  };

  const getIconForType = () => {
    switch (config.type) {
      case 'success': return '✓';
      case 'error': return '✕';
      case 'warning': return '⚠';
      case 'info': return 'ℹ';
      default: return 'ℹ';
    }
  };

  return (
    <div className={styles.modalContent}>
      <div className={`${styles.alertHeader} ${styles[config.type]}`}>
        <div className={styles.alertIcon}>
          {getIconForType()}
        </div>
        <h2 className={styles.alertTitle}>{config.title}</h2>
      </div>
      
      <div className={styles.alertBody}>
        <p className={styles.alertMessage}>{config.message}</p>
      </div>
      
      <div className={styles.modalFooter}>
        <button 
          className={`${styles.button} ${styles.primaryButton}`}
          onClick={handleConfirm}
        >
          {config.buttonText || 'OK'}
        </button>
      </div>
    </div>
  );
}