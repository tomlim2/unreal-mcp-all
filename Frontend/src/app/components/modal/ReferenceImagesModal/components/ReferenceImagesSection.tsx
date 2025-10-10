/**
 * Reference Images Section Component
 * Grid of reference image upload slots
 */

import { ReferenceImageSlot } from './ReferenceImageSlot';
import { ReferenceImageUpload } from '../../../modal/types';
import { MAX_REFERENCE_IMAGES } from '../utils/constants';
import styles from '../ReferenceImagesModal.module.css';

interface ReferenceImagesSectionProps {
  referenceImages: ReferenceImageUpload[];
  referencePrompts: string[];
  fileInputRefs: React.MutableRefObject<(HTMLInputElement | null)[]>;
  onFileUpload: (index: number, file: File | null) => void;
  onPromptChange: (index: number, prompt: string) => void;
  onRemove: (index: number) => void;
  submitting: boolean;
}

export function ReferenceImagesSection({
  referenceImages,
  referencePrompts,
  fileInputRefs,
  onFileUpload,
  onPromptChange,
  onRemove,
  submitting
}: ReferenceImagesSectionProps) {
  return (
    <div className={styles.section}>
      <h3>Reference Images (max {MAX_REFERENCE_IMAGES})</h3>
      <p className={styles.description}>
        Upload images and provide specific prompts for how each should influence the transformation.
      </p>

      <div className={styles.referenceGrid}>
        {[0, 1, 2].map((index) => (
          <ReferenceImageSlot
            key={index}
            index={index}
            image={referenceImages[index]}
            prompt={referencePrompts[index] || ''}
            fileInputRef={(el) => (fileInputRefs.current[index] = el)}
            onFileUpload={onFileUpload}
            onPromptChange={onPromptChange}
            onRemove={onRemove}
            submitting={submitting}
          />
        ))}
      </div>
    </div>
  );
}
