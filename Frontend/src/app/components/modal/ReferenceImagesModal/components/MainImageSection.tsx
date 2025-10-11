/**
 * Main Image Section Component
 * Target image section with display and slider
 */

import { MainImageDisplay } from './MainImageDisplay';
import { ImageSlider } from './ImageSlider';
import { SelectedImage, SessionImageInfo } from '../types';
import styles from '../ReferenceImagesModal.module.css';

interface MainImageSectionProps {
  selectedImage: SelectedImage;
  sessionImages: SessionImageInfo[];
  selectedImageIndex: number;
  mainImageInputRef: React.RefObject<HTMLInputElement>;
  onMainImageUpload: (file: File | null) => void;
  onRemoveMainImageUpload: () => void;
  onSetSelectedImageIndex: (index: number) => void;
  onSelectSessionImage: (index: number) => void;
  onSelectUpload: () => void;
  submitting: boolean;
}

export function MainImageSection({
  selectedImage,
  sessionImages,
  selectedImageIndex,
  mainImageInputRef,
  onMainImageUpload,
  onRemoveMainImageUpload,
  onSetSelectedImageIndex,
  onSelectSessionImage,
  onSelectUpload,
  submitting
}: MainImageSectionProps) {
  return (
    <div className={styles.section}>
      <h3>Target Image (Main Image to Transform)</h3>

      {/* Main Image Display */}
      <div className={styles.mainImageDisplay}>
        <MainImageDisplay
          selectedImage={selectedImage}
          onClearUpload={onRemoveMainImageUpload}
          onClearSession={() => onSetSelectedImageIndex(-1)}
          onFileUpload={onMainImageUpload}
        />
      </div>

      {/* Image Slider */}
      <ImageSlider
        sessionImages={sessionImages}
        selectedIndex={selectedImageIndex}
        onSelectUpload={onSelectUpload}
        onSelectImage={onSelectSessionImage}
      />

      {/* Hidden file input */}
      <input
        ref={mainImageInputRef}
        type="file"
        accept="image/*"
        onChange={(e) => onMainImageUpload(e.target.files?.[0] || null)}
        style={{ display: 'none' }}
        disabled={submitting}
      />
    </div>
  );
}
