/**
 * Reference Images Modal - Main Component
 * Orchestrates the modal with all sub-components
 */

'use client';

import { useState, useEffect } from 'react';
import { ReferenceImagesModalConfig, ReferenceImagesData } from '../types';
import { useSessionImageData } from './hooks/useSessionImageData';
import { useImageSelection } from './hooks/useImageSelection';
import { useReferenceImages } from './hooks/useReferenceImages';
import { MainImageSection } from './components/MainImageSection';
import { MainPromptSection } from './components/MainPromptSection';
import { ReferenceImagesSection } from './components/ReferenceImagesSection';
import { fileToDataUri } from './utils/imageUtils';
import { revokePreviewUrl } from './utils/imageUtils';
import styles from './ReferenceImagesModal.module.css';

interface ReferenceImagesModalProps {
  config: ReferenceImagesModalConfig;
  onClose: (data?: ReferenceImagesData) => void;
}

export default function ReferenceImagesModal({ config, onClose }: ReferenceImagesModalProps) {
  const { sessionId, onSubmit } = config;

  // Hooks
  const { latestImage, sessionImages, loading } = useSessionImageData(sessionId);
  const {
    selectedImageIndex,
    mainImageUpload,
    mainImageInputRef,
    handleMainImageUpload,
    removeMainImageUpload,
    handleSelectSessionImage,
    handleSelectUpload,
    getSelectedImage,
    setSelectedImageIndex
  } = useImageSelection(sessionImages);
  const {
    referenceImages,
    referencePrompts,
    fileInputRefs,
    handleFileUpload,
    handleReferencePromptChange,
    removeReferenceImage
  } = useReferenceImages();

  // Local state
  const [mainPrompt, setMainPrompt] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (mainImageUpload?.preview) {
        revokePreviewUrl(mainImageUpload.preview);
      }
      referenceImages.forEach(ref => {
        if (ref.preview) {
          revokePreviewUrl(ref.preview);
        }
      });
    };
  }, [mainImageUpload, referenceImages]);

  // Handle submit
  const handleSubmit = async () => {
    const selectedImage = getSelectedImage();
    const hasTargetImage = selectedImage?.type === 'session';
    const hasMainImageUpload = selectedImage?.type === 'upload';
    const hasPrompts = mainPrompt.trim() || referencePrompts.some(p => p.trim());

    if (!hasPrompts) {
      alert('Please enter at least one prompt (main prompt or reference prompts)');
      return;
    }

    const isTextToImage = !hasTargetImage && !hasMainImageUpload && referenceImages.length === 0;

    setSubmitting(true);

    try {
      // Convert main image upload to base64 if provided
      let mainImageData = undefined;
      if (mainImageUpload) {
        try {
          const dataUri = await fileToDataUri(mainImageUpload.file);
          mainImageData = {
            data: dataUri,
            mime_type: mainImageUpload.file.type
          };
        } catch (error) {
          console.error('Failed to convert main image:', error);
          alert('Failed to process main image. Please try again.');
          setSubmitting(false);
          return;
        }
      }

      // Convert all reference images to base64 (skip undefined entries in sparse array)
      const referenceImageData = [];
      const activeReferencePrompts = [];
      for (let i = 0; i < referenceImages.length; i++) {
        const refImage = referenceImages[i];
        if (!refImage) continue; // Skip undefined entries

        try {
          const dataUri = await fileToDataUri(refImage.file);
          referenceImageData.push({
            data: dataUri,
            mime_type: refImage.file.type
          });
          activeReferencePrompts.push(referencePrompts[i] || '');
        } catch (error) {
          console.error(`Failed to convert reference image ${i + 1}:`, error);
          alert(`Failed to process reference image ${i + 1}. Please try again.`);
          setSubmitting(false);
          return;
        }
      }

      const data: ReferenceImagesData = {
        prompt: mainPrompt.trim() || 'Transform using reference images',
        main_prompt: mainPrompt.trim() || undefined,
        reference_prompts: activeReferencePrompts,
        targetImageUid: isTextToImage ? undefined : (hasTargetImage && selectedImage?.type === 'session' ? selectedImage.uid : undefined),
        mainImageData: mainImageData,
        referenceImageData
      };

      console.log('ReferenceImagesModal: Submitting data:', {
        mode: isTextToImage ? '🎨 TEXT-TO-IMAGE' : '🖼️ IMAGE-TO-IMAGE',
        prompt: data.prompt,
        main_prompt: data.main_prompt,
        reference_prompts: data.reference_prompts,
        targetImageUid: data.targetImageUid,
        mainImageData: mainImageData ? 'present' : 'none',
        referenceImageData: data.referenceImageData?.length || 0,
        isTextToImage: isTextToImage
      });

      await onSubmit(data);
      onClose(data);
    } catch (error) {
      console.error('Error submitting reference images:', error);
      alert('Failed to submit request. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleClose = () => {
    onClose();
  };

  if (loading) {
    return (
      <div className={styles.modal}>
        <div className={styles.modalContent}>
          <div className={styles.loading}>
            <div className={styles.spinner}></div>
            <p>Loading latest image...</p>
          </div>
        </div>
      </div>
    );
  }

  const selectedImage = getSelectedImage();

  return (
    <div className={styles.modal}>
      <div className={styles.modalContent}>
        <div className={styles.header}>
          <h2>Image to Image with Reference Images</h2>
          <button className={styles.closeButton} onClick={handleClose}>×</button>
        </div>

        <div className={styles.body}>
          {/* Main Image Section */}
          <MainImageSection
            selectedImage={selectedImage}
            sessionImages={sessionImages}
            selectedImageIndex={selectedImageIndex}
            mainImageInputRef={mainImageInputRef}
            onMainImageUpload={handleMainImageUpload}
            onRemoveMainImageUpload={removeMainImageUpload}
            onSetSelectedImageIndex={setSelectedImageIndex}
            onSelectSessionImage={handleSelectSessionImage}
            onSelectUpload={handleSelectUpload}
            submitting={submitting}
          />

          {/* Main Prompt Section */}
          <MainPromptSection
            value={mainPrompt}
            onChange={setMainPrompt}
            disabled={submitting}
          />

          {/* Reference Images Section */}
          <ReferenceImagesSection
            referenceImages={referenceImages}
            referencePrompts={referencePrompts}
            fileInputRefs={fileInputRefs}
            onFileUpload={handleFileUpload}
            onPromptChange={handleReferencePromptChange}
            onRemove={removeReferenceImage}
            submitting={submitting}
          />
        </div>

        {/* Footer */}
        <div className={styles.footer}>
          <button
            className={styles.button}
            onClick={handleClose}
            disabled={submitting}
          >
            Cancel
          </button>
          <button
            className={`${styles.button} ${styles.primaryButton}`}
            onClick={handleSubmit}
            disabled={submitting}
          >
            {submitting ? 'Submitting...' : 'Submit'}
          </button>
        </div>
      </div>
    </div>
  );
}
