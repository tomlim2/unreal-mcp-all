'use client';

import { FormModalConfig } from './types';
import styles from './Modal.module.css';

interface FormModalProps {
  config: FormModalConfig;
}

export default function FormModal({ config }: FormModalProps) {
  return (
    <div className={styles.modalContent}>
      <div className={styles.formHeader}>
        <h2 className={styles.formTitle}>{config.title}</h2>
      </div>
      
      <div className={styles.formBody}>
        {config.component}
      </div>
      
      <div className={styles.modalFooter}>
        <button 
          className={`${styles.button} ${styles.secondaryButton}`}
          onClick={config.onClose}
          disabled={config.loading}
        >
          {config.cancelText || 'Cancel'}
        </button>
        <button 
          className={`${styles.button} ${styles.primaryButton}`}
          type="submit"
          form="form-modal-form"
          disabled={config.loading}
        >
          {config.loading ? 'Loading...' : (config.submitText || 'Submit')}
        </button>
      </div>
    </div>
  );
}