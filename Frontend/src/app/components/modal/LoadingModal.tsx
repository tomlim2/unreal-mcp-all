'use client';

import { LoadingModalConfig } from './types';
import styles from './Modal.module.css';

interface LoadingModalProps {
  config: LoadingModalConfig;
}

export default function LoadingModal({ config }: LoadingModalProps) {
  return (
    <div className={styles.modalContent}>
      <div className={styles.loadingHeader}>
        <div className={styles.spinner}></div>
        <h2 className={styles.loadingTitle}>{config.message}</h2>
      </div>
      
      {typeof config.progress === 'number' && (
        <div className={styles.progressContainer}>
          <div className={styles.progressBar}>
            <div 
              className={styles.progressFill}
              style={{ width: `${Math.max(0, Math.min(100, config.progress))}%` }}
            ></div>
          </div>
          <span className={styles.progressText}>
            {Math.round(config.progress)}%
          </span>
        </div>
      )}
      
      {config.cancellable && (
        <div className={styles.modalFooter}>
          <button 
            className={`${styles.button} ${styles.secondaryButton}`}
            onClick={config.onCancel}
          >
            Cancel
          </button>
        </div>
      )}
    </div>
  );
}