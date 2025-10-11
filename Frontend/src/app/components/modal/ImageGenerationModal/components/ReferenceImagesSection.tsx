/**
 * Reference Images Section Component
 * Grid of reference image upload slots (simplified - no per-image prompts)
 */

import { ReferenceImageSlot } from './ReferenceImageSlot';
import { ReferenceImageUpload } from '../../../modal/types';
import { MAX_REFERENCE_IMAGES } from '../utils/constants';
import styles from '../ImageGenerationModal.module.css';

interface ReferenceImagesSectionProps {
  referenceImages: ReferenceImageUpload[];
  fileInputRefs: React.MutableRefObject<(HTMLInputElement | null)[]>;
  onFileUpload: (index: number, file: File | null) => void;
  onRemove: (index: number) => void;
  submitting: boolean;
}

export function ReferenceImagesSection({
  referenceImages,
  fileInputRefs,
  onFileUpload,
  onRemove,
  submitting
}: ReferenceImagesSectionProps) {
  return (
    <div className={styles.section}>
      <h3>Reference Images (max {MAX_REFERENCE_IMAGES})</h3>
      <p className={styles.description}>
        Upload reference images to influence the visual style of the generated image.
      </p>

      <div className={styles.referenceGrid}>
        {[0, 1, 2].map((index) => (
          <ReferenceImageSlot
            key={index}
            index={index}
            image={referenceImages[index]}
            fileInputRef={(el) => (fileInputRefs.current[index] = el)}
            onFileUpload={onFileUpload}
            onRemove={onRemove}
            submitting={submitting}
          />
        ))}
      </div>
    </div>
  );
}
