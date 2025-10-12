/**
 * Image Slider Component
 * Horizontal thumbnail slider for session images
 */

import { SessionImageInfo } from '../types';
import { getFullImageUrl } from '../utils/imageUtils';
import styles from '../ImageGenerationModal.module.css';

interface ImageSliderProps {
  sessionImages: SessionImageInfo[];
  selectedIndex: number;
  onSelectImage: (index: number) => void;
}

export function ImageSlider({ sessionImages, selectedIndex, onSelectImage }: ImageSliderProps) {
  return (
    <div className={styles.imageSlider}>
      <div className={styles.sliderTrack}>
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
