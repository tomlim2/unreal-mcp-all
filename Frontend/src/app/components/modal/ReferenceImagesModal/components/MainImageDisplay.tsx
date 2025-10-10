/**
 * Main Image Display Component
 * Shows the selected image with info bar and clear button
 */

import { SelectedImage } from "../types";
import styles from "../ReferenceImagesModal.module.css";

interface MainImageDisplayProps {
  selectedImage: SelectedImage;
  onClearUpload: () => void;
  onClearSession: () => void;
}

export function MainImageDisplay({
  selectedImage,
  onClearUpload,
  onClearSession,
}: MainImageDisplayProps) {
  if (!selectedImage) {
    return (
      <div className={styles.mainImagePlaceholder}>
        <span>Select an image from below or upload a new one</span>
      </div>
    );
  }

  if (selectedImage.type === "upload") {
    return (
      <div className={styles.mainImageContainer}>
        <div className={styles.mainImageWrapper}>
          <img
            src={selectedImage.preview}
            alt="Uploaded image to transform"
            className={styles.mainImage}
          />
        </div>
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
      </div>
    );
  }

  return (
    <div className={styles.mainImageContainer}>
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
        />
      </div>
    </div>
  );
}
