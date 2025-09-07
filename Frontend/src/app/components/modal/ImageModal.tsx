'use client';

import { ImageModalConfig } from './types';
import styles from './Modal.module.css';

interface ImageModalProps {
  config: ImageModalConfig;
}

export default function ImageModal({ config }: ImageModalProps) {
  const handleDownload = () => {
    const link = document.createElement('a');
    link.href = config.src;
    link.download = config.downloadFilename || 'download';
    link.target = '_blank';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className={styles.modalContent}>
      <div className={styles.imageContainer}>
        <img 
          src={config.src} 
          alt={config.alt}
          className={styles.modalImage}
        />
      </div>
      
      {(config.caption || config.downloadable) && (
        <div className={styles.imageFooter}>
          {config.caption && (
            <p className={styles.imageCaption}>{config.caption}</p>
          )}
          {config.downloadable && (
            <button 
              className={`${styles.button} ${styles.secondaryButton}`}
              onClick={handleDownload}
            >
              Download
            </button>
          )}
        </div>
      )}
    </div>
  );
}