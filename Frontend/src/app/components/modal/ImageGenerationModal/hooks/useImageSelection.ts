/**
 * Hook for main image selection (session images + uploaded image)
 */

import { useState, useRef } from 'react';
import { SessionImageInfo, SelectedImage } from '../types';
import { validateImageFile, createPreviewUrl, revokePreviewUrl, getFullImageUrl } from '../utils/imageUtils';

export function useImageSelection(sessionImages: SessionImageInfo[]) {
  const [selectedImageIndex, setSelectedImageIndex] = useState<number>(-1); // -1 = upload, 0+ = session image
  const [mainImageUpload, setMainImageUpload] = useState<{ file: File; preview: string } | null>(null);
  const mainImageInputRef = useRef<HTMLInputElement | null>(null);

  // Handle main image upload
  const handleMainImageUpload = async (file: File | null) => {
    if (!file) return;

    // Validate file
    const validation = validateImageFile(file);
    if (!validation.valid) {
      alert(validation.error);
      return;
    }

    // Create preview
    const preview = createPreviewUrl(file);

    // Clean up old preview if exists
    if (mainImageUpload?.preview) {
      revokePreviewUrl(mainImageUpload.preview);
    }

    setMainImageUpload({ file, preview });
    setSelectedImageIndex(-1); // Select upload button
  };

  // Remove main image upload
  const removeMainImageUpload = () => {
    if (mainImageUpload?.preview) {
      revokePreviewUrl(mainImageUpload.preview);
    }
    setMainImageUpload(null);
    setSelectedImageIndex(-1);
    // Reset file input to allow re-uploading the same file
    if (mainImageInputRef.current) {
      mainImageInputRef.current.value = '';
    }
  };

  // Handle selecting a session image from slider
  const handleSelectSessionImage = (index: number) => {
    setSelectedImageIndex(index);
    // Clear uploaded image when switching to UID
    if (mainImageUpload) {
      if (mainImageUpload.preview) {
        revokePreviewUrl(mainImageUpload.preview);
      }
      setMainImageUpload(null);
    }
  };

  // Get currently selected image for main display
  const getSelectedImage = (): SelectedImage => {
    if (selectedImageIndex === -1 && mainImageUpload) {
      return { type: 'upload' as const, preview: mainImageUpload.preview };
    }
    if (selectedImageIndex >= 0 && selectedImageIndex < sessionImages.length) {
      const sessionImage = sessionImages[selectedImageIndex];
      return {
        type: 'session' as const,
        url: getFullImageUrl(sessionImage.url),
        uid: sessionImage.uid,
        filename: sessionImage.filename
      };
    }
    return null;
  };

  return {
    selectedImageIndex,
    mainImageUpload,
    mainImageInputRef,
    handleMainImageUpload,
    removeMainImageUpload,
    handleSelectSessionImage,
    getSelectedImage,
    setSelectedImageIndex
  };
}
