'use client';

import { CustomModalConfig } from './types';
import styles from './Modal.module.css';

interface CustomModalProps {
  config: CustomModalConfig;
}

export default function CustomModal({ config }: CustomModalProps) {
  return (
    <div className={styles.modalContent}>
      {config.title && (
        <div className={styles.customHeader}>
          <h2 className={styles.customTitle}>{config.title}</h2>
        </div>
      )}
      
      <div className={styles.customBody}>
        {config.component}
      </div>
      
      {config.footer && (
        <div className={styles.modalFooter}>
          {config.footer}
        </div>
      )}
    </div>
  );
}