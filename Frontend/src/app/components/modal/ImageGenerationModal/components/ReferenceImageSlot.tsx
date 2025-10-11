/**
 * Reference Image Slot Component
 * Individual reference image upload slot (simplified - no per-image prompt)
 */

import { useState } from 'react';
import { ReferenceImageUpload } from '../../../modal/types';
import styles from '../ImageGenerationModal.module.css';

interface ReferenceImageSlotProps {
  index: number;
  image: ReferenceImageUpload | undefined;
  fileInputRef: (el: HTMLInputElement | null) => void;
  onFileUpload: (index: number, file: File | null) => void;
  onRemove: (index: number) => void;
  submitting: boolean;
}

export function ReferenceImageSlot({
  index,
  image,
  fileInputRef,
  onFileUpload,
  onRemove,
  submitting
}: ReferenceImageSlotProps) {
  const [isDragOver, setIsDragOver] = useState(false);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (file.type.startsWith('image/')) {
        onFileUpload(index, file);
      }
    }
  };
  return (
    <div className={styles.referenceSlot}>
      {image ? (
        <>
          <div
            className={`${styles.uploadArea} ${styles.dragDropZone} ${isDragOver ? styles.dragOver : ''}`}
            onDragOver={handleDragOver}
            onDragEnter={handleDragEnter}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <div className={styles.uploadedImage}>
              <img
                src={image.preview}
                alt={`Reference ${index + 1}`}
                className={styles.referencePreview}
              />
            </div>
          </div>
          <div className={styles.referenceImageInfo}>
            <span className={styles.referenceImageName}>Reference {index + 1}</span>
            <button
              className={styles.referenceRemoveButton}
              onClick={() => onRemove(index)}
              disabled={submitting}
              title="Remove reference image"
            >
              ×
            </button>
          </div>
        </>
      ) : (
        <div
          className={`${styles.uploadArea} ${styles.dragDropZone} ${isDragOver ? styles.dragOver : ''}`}
          onDragOver={handleDragOver}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <div
            className={styles.uploadPlaceholder}
            onClick={() => {
              const input = document.querySelector(`input[data-index="${index}"]`) as HTMLInputElement;
              input?.click();
            }}
          >
            <span className={styles.uploadIcon}>+</span>
            <span>Upload Image</span>
          </div>
        </div>
      )}

      <input
        ref={fileInputRef}
        data-index={index}
        type="file"
        accept="image/*"
        onChange={(e) => onFileUpload(index, e.target.files?.[0] || null)}
        style={{ display: 'none' }}
        disabled={submitting}
      />
    </div>
  );
}
