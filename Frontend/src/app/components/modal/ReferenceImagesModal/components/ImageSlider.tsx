/**
 * Image Slider Component
 * Horizontal thumbnail slider for session images
 */

import { SessionImageInfo } from '../types';
import { getFullImageUrl } from '../utils/imageUtils';
import styles from '../ReferenceImagesModal.module.css';

interface ImageSliderProps {
  sessionImages: SessionImageInfo[];
  selectedIndex: number;
  onSelectUpload: () => void;
  onSelectImage: (index: number) => void;
}

export function ImageSlider({ sessionImages, selectedIndex, onSelectUpload, onSelectImage }: ImageSliderProps) {
  return (
    <div className={styles.imageSlider}>
      <div className={styles.sliderTrack}>
        {/* Upload Button */}
        <div
          className={`${styles.sliderItem} ${styles.sliderItemUpload} ${
            selectedIndex === -1 ? styles.sliderItemSelected : ''
          }`}
          onClick={onSelectUpload}
        >
          <span className={styles.uploadIcon}>+</span>
          <span className={styles.uploadText}>Upload</span>
        </div>

        {/* Session Images */}
        {sessionImages.map((image, index) => (
          <div
            key={image.uid}
            className={`${styles.sliderItem} ${
              selectedIndex === index ? styles.sliderItemSelected : ''
            }`}
            onClick={() => onSelectImage(index)}
          >
            <img
              src={getFullImageUrl(image.thumbnail_url)}
              alt={`Session image ${image.uid}`}
              className={styles.sliderThumbnail}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
