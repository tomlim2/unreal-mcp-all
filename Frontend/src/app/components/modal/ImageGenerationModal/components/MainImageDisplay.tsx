/**
 * Main Image Display Component
 * Shows the selected image with info bar and clear button
 */

import { useState } from 'react';
import { SelectedImage } from "../types";
import styles from "../ImageGenerationModal.module.css";

interface MainImageDisplayProps {
  selectedImage: SelectedImage;
  onClearUpload: () => void;
  onClearSession: () => void;
  onFileUpload?: (file: File) => void;
  fileInputRef?: React.RefObject<HTMLInputElement>;
}

export function MainImageDisplay({
  selectedImage,
  onClearUpload,
  onClearSession,
  onFileUpload,
  fileInputRef,
}: MainImageDisplayProps) {
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
    if (files && files.length > 0 && onFileUpload) {
      const file = files[0];
      if (file.type.startsWith('image/')) {
        onFileUpload(file);
      }
    }
  };

  const handleClick = () => {
    if (!selectedImage) {
      fileInputRef?.current?.click();
    }
  };

  if (!selectedImage) {
    return (
      <div
        className={`${styles.mainImagePlaceholder} ${styles.dragDropZone} ${isDragOver ? styles.dragOver : ''}`}
        onClick={handleClick}
        onDragOver={handleDragOver}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <div className={styles.uploadIcon}>+</div>
        <span>Click or drag and drop to upload image</span>
      </div>
    );
  }

  if (selectedImage.type === "upload") {
    return (
      <div
        className={`${styles.mainImageContainer} ${styles.dragDropZone} ${isDragOver ? styles.dragOver : ''}`}
        onDragOver={handleDragOver}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
		<div className={styles.imageInfo}>
          <span className={styles.filename}>Uploaded Image</span>
          <button
            className={styles.clearImageButton}
            onClick={onClearUpload}
            title="Clear uploaded image"
          >
            ×
          </button>
        </div>
        <div className={styles.mainImageWrapper}>
          <img
            src={selectedImage.preview}
            alt="Uploaded image to transform"
            className={styles.mainImage}
            draggable={false}
          />
        </div>
      </div>
    );
  }

  return (
    <div
      className={`${styles.mainImageContainer} ${styles.dragDropZone} ${isDragOver ? styles.dragOver : ''}`}
      onDragOver={handleDragOver}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <div className={styles.imageInfo}>
        <div className={styles.imageInfoLeft}>
          <span className={styles.uid}>{selectedImage.uid}</span>
          <span className={styles.filename}>{selectedImage.filename}</span>
        </div>
        <button
          className={styles.clearImageButton}
          onClick={onClearSession}
          title="Clear selected image"
        >
          ×
        </button>
      </div>
      <div className={styles.mainImageWrapper}>
        <img
          src={selectedImage.url}
          alt={`Session image ${selectedImage.uid}`}
          className={styles.mainImage}
          draggable={false}
        />
      </div>
    </div>
  );
}
