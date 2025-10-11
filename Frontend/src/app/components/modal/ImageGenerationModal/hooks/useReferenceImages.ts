/**
 * Hook for managing reference images (simplified - no per-image prompts)
 */

import { useState, useRef } from 'react';
import { ReferenceImageUpload } from '../../../modal/types';
import { validateImageFile, createPreviewUrl, revokePreviewUrl } from '../utils/imageUtils';

export function useReferenceImages() {
  const [referenceImages, setReferenceImages] = useState<ReferenceImageUpload[]>([]);
  const fileInputRefs = useRef<(HTMLInputElement | null)[]>([]);

  // Handle file upload - client-side only processing
  const handleFileUpload = async (index: number, file: File | null) => {
    if (!file) return;

    // Validate file
    const validation = validateImageFile(file);
    if (!validation.valid) {
      alert(validation.error);
      return;
    }

    // Create preview
    const preview = createPreviewUrl(file);

    // Update reference images array - no server upload yet
    const newReferenceImages = [...referenceImages];
    newReferenceImages[index] = {
      file,
      preview
    };
    setReferenceImages(newReferenceImages);
  };

  // Remove reference image
  const removeReferenceImage = (index: number) => {
    // Revoke the preview URL to free memory
    if (referenceImages[index]?.preview) {
      revokePreviewUrl(referenceImages[index].preview!);
    }

    // Create new array and set the specific index to undefined (sparse array)
    const newReferenceImages = [...referenceImages];
    delete newReferenceImages[index];
    setReferenceImages(newReferenceImages);
  };

  return {
    referenceImages,
    fileInputRefs,
    handleFileUpload,
    removeReferenceImage
  };
}
