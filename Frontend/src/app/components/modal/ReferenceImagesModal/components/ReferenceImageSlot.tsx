/**
 * Reference Image Slot Component
 * Individual reference image upload slot with prompt
 */

import { ReferenceImageUpload } from '../../../modal/types';
import { MAX_REFERENCE_PROMPT_LENGTH } from '../utils/constants';
import styles from '../ReferenceImagesModal.module.css';

interface ReferenceImageSlotProps {
  index: number;
  image: ReferenceImageUpload | undefined;
  prompt: string;
  fileInputRef: (el: HTMLInputElement | null) => void;
  onFileUpload: (index: number, file: File | null) => void;
  onPromptChange: (index: number, prompt: string) => void;
  onRemove: (index: number) => void;
  submitting: boolean;
}

export function ReferenceImageSlot({
  index,
  image,
  prompt,
  fileInputRef,
  onFileUpload,
  onPromptChange,
  onRemove,
  submitting
}: ReferenceImageSlotProps) {
  return (
    <div className={styles.referenceSlot}>
      {image ? (
        <>
          <div className={styles.uploadArea}>
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
        <div className={styles.uploadArea}>
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

      {image && (
        <div className={styles.referencePromptContainer}>
          <textarea
            value={prompt}
            onChange={(e) => onPromptChange(index, e.target.value)}
            placeholder={`How should this reference image influence the transformation? (e.g., "Apply the cyberpunk neon lighting style")`}
            className={styles.referencePromptTextarea}
            rows={2}
            disabled={submitting}
          />
          <div className={styles.characterCount}>
            {prompt.length}/{MAX_REFERENCE_PROMPT_LENGTH} characters
            {prompt.length > MAX_REFERENCE_PROMPT_LENGTH && (
              <span className={styles.warning}> (exceeds recommended limit)</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
