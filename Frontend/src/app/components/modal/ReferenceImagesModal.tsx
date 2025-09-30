'use client';

import { useState, useEffect, useRef } from 'react';
import { ReferenceImagesModalConfig, ReferenceImagesData, ReferenceImageUpload } from './types';
import styles from './ReferenceImagesModal.module.css';

// Import the URL transformation function to handle backend/frontend routing
function getFullImageUrl(imageUrl: string): string {
  // If it's already an absolute URL, return as-is
  if (imageUrl.startsWith("http://") || imageUrl.startsWith("https://")) {
    return imageUrl;
  }

  // Support for screenshot URLs (both /api/screenshot/ and /api/screenshot-file/)
  if (imageUrl.startsWith("/api/screenshot/") || imageUrl.startsWith("/api/screenshot-file/")) {
    const httpBridgePort = process.env.NEXT_PUBLIC_HTTP_BRIDGE_PORT || "8080";
    const fullUrl = `http://localhost:${httpBridgePort}${imageUrl}`;
    console.log("Generated direct URL:", fullUrl);
    return fullUrl;
  }

  // Otherwise return as-is
  return imageUrl;
}

interface LatestImageInfo {
  uid: string | null;
  filename: string | null;
  thumbnail_url: string | null;
  available: boolean;
}

interface ReferenceImagesModalProps {
  config: ReferenceImagesModalConfig;
  onClose: (data?: ReferenceImagesData) => void;
}

export default function ReferenceImagesModal({ config, onClose }: ReferenceImagesModalProps) {
  const { sessionId, onSubmit } = config;

  const [latestImage, setLatestImage] = useState<LatestImageInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  // Form state
  const [mainPrompt, setMainPrompt] = useState('');
  const [referenceImages, setReferenceImages] = useState<ReferenceImageUpload[]>([]);
  const [referencePrompts, setReferencePrompts] = useState<string[]>(['', '', '']); // Individual prompts for each reference image

  const fileInputRefs = useRef<(HTMLInputElement | null)[]>([]);
  const imageUrlRef = useRef<string | null>(null);

  // Fetch latest image info - only once on mount
  useEffect(() => {
    async function fetchLatestImage() {
      try {
        const httpBridgePort = process.env.NEXT_PUBLIC_HTTP_BRIDGE_PORT || '8080';
        const response = await fetch(`http://localhost:${httpBridgePort}/api/session/${sessionId}/latest-image`);
        const data = await response.json();

        if (data.success) {
          setLatestImage(data.latest_image);
          // Cache the image URL to prevent reloading
          if (data.latest_image.thumbnail_url) {
            imageUrlRef.current = getFullImageUrl(data.latest_image.thumbnail_url);
          }
        } else {
          console.error('Failed to fetch latest image:', data.error);
          setLatestImage({ uid: null, filename: null, thumbnail_url: null, available: false });
        }
      } catch (error) {
        console.error('Error fetching latest image:', error);
        setLatestImage({ uid: null, filename: null, thumbnail_url: null, available: false });
      } finally {
        setLoading(false);
      }
    }

    fetchLatestImage();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Only run once on mount

  // Handle file upload - client-side only processing
  const handleFileUpload = async (index: number, file: File | null) => {
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file');
      return;
    }

    // Validate file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
      alert('Image must be smaller than 10MB');
      return;
    }

    // Create preview
    const preview = URL.createObjectURL(file);

    // Update reference images array - no server upload yet
    const newReferenceImages = [...referenceImages];
    newReferenceImages[index] = {
      file,
      purpose: newReferenceImages[index]?.purpose || 'style', // Keep for backward compatibility
      preview,
      uploading: false,  // No uploading state needed
      refer_uid: undefined  // Will be generated on submit
    };
    setReferenceImages(newReferenceImages);
  };

  // Upload reference image and get refer_uid
  const uploadReferenceImage = async (file: File, purpose: string): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = async () => {
        try {
          const base64Data = (reader.result as string).split(',')[1];
          const httpBridgePort = process.env.NEXT_PUBLIC_HTTP_BRIDGE_PORT || '8080';

          const response = await fetch(`http://localhost:${httpBridgePort}/api/reference-images`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              action: 'upload_reference_image',
              session_id: sessionId,
              image_data: base64Data,
              purpose,
              mime_type: file.type
            })
          });

          const data = await response.json();

          if (data.success && data.refer_uid) {
            resolve(data.refer_uid);
          } else {
            reject(new Error(data.error || 'Failed to upload reference image'));
          }
        } catch (error) {
          reject(error);
        }
      };
      reader.onerror = () => reject(new Error('Failed to read file'));
      reader.readAsDataURL(file);
    });
  };

  // Handle purpose change - client-side only (keep for backward compatibility)
  const handlePurposeChange = (index: number, purpose: 'style' | 'color' | 'composition') => {
    const newReferenceImages = [...referenceImages];
    if (newReferenceImages[index]) {
      newReferenceImages[index].purpose = purpose;
      setReferenceImages([...newReferenceImages]);
    }
  };

  // Handle reference prompt change - new functionality
  const handleReferencePromptChange = (index: number, promptText: string) => {
    const newReferencePrompts = [...referencePrompts];
    newReferencePrompts[index] = promptText;
    setReferencePrompts(newReferencePrompts);
  };

  // Remove reference image
  const removeReferenceImage = (index: number) => {
    const newReferenceImages = [...referenceImages];
    if (newReferenceImages[index]?.preview) {
      URL.revokeObjectURL(newReferenceImages[index].preview!);
    }
    newReferenceImages.splice(index, 1);
    setReferenceImages(newReferenceImages);

    // Also clear the corresponding prompt
    const newReferencePrompts = [...referencePrompts];
    newReferencePrompts[index] = '';
    setReferencePrompts(newReferencePrompts);
  };

  // Handle submit - upload all images at once
  const handleSubmit = async () => {
    if (!latestImage?.available || !latestImage.uid) {
      alert('No target image available');
      return;
    }

    if (!mainPrompt.trim() && referencePrompts.every(p => !p.trim())) {
      alert('Please enter at least one prompt (main prompt or reference prompts)');
      return;
    }

    setSubmitting(true);

    try {
      // Upload all reference images to get refer_uids
      const referenceImageUids = [];

      for (let i = 0; i < referenceImages.length; i++) {
        const refImage = referenceImages[i];
        try {
          const refer_uid = await uploadReferenceImage(refImage.file, refImage.purpose);
          referenceImageUids.push(refer_uid);
        } catch (error) {
          console.error(`Failed to upload reference image ${i + 1}:`, error);
          alert(`Failed to upload reference image ${i + 1}. Please try again.`);
          setSubmitting(false);
          return;
        }
      }

      // Collect only prompts for uploaded images
      const activeReferencePrompts = referenceImages.map((_, index) =>
        referencePrompts[index] || ''
      );

      console.log('🔍 DEBUG Reference Prompts:', {
        referencePromptsState: referencePrompts,
        referenceImagesCount: referenceImages.length,
        activeReferencePrompts: activeReferencePrompts
      });

      const data: ReferenceImagesData = {
        prompt: mainPrompt.trim() || 'Transform using reference images', // Minimal backward compatibility
        main_prompt: mainPrompt.trim() || undefined, // NEW: Optional main prompt
        reference_prompts: activeReferencePrompts, // NEW: Individual prompts per image
        targetImageUid: latestImage.uid,
        referenceImages, // Keep for legacy compatibility
        referenceImageUids // New UID-based field
      };

      console.log('ReferenceImagesModal: Submitting data with enhanced prompts:', {
        prompt: data.prompt,
        main_prompt: data.main_prompt,
        reference_prompts: data.reference_prompts,
        targetImageUid: data.targetImageUid,
        referenceImageUids: data.referenceImageUids?.length || 0,
        referenceImages: data.referenceImages?.length || 0
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

  // Handle close
  const handleClose = () => {
    // Clean up preview URLs
    referenceImages.forEach(ref => {
      if (ref.preview) {
        URL.revokeObjectURL(ref.preview);
      }
    });
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

  if (!latestImage?.available) {
    return (
      <div className={styles.modal}>
        <div className={styles.modalContent}>
          <div className={styles.header}>
            <h2>Reference Images</h2>
            <button className={styles.closeButton} onClick={handleClose}>×</button>
          </div>

          <div className={styles.noImagesState}>
            <div className={styles.warningIcon}>⚠️</div>
            <h3>No recent images available</h3>
            <p>Take a screenshot or generate an image first to use this feature</p>

            <div className={styles.actions}>
              <button className={styles.button} onClick={handleClose}>
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.modal}>
      <div className={styles.modalContent}>
        <div className={styles.header}>
          <h2>Image to Image with Reference Images</h2>
          <button className={styles.closeButton} onClick={handleClose}>×</button>
        </div>

        <div className={styles.body}>
          {/* Target Image Section */}
          <div className={styles.section}>
            <h3>Target Image</h3>
            <div className={styles.targetImage}>
              <img
                src={imageUrlRef.current || getFullImageUrl(latestImage.thumbnail_url!)}
                alt={`Image ${latestImage.uid}`}
                className={styles.thumbnail}
              />
              <div className={styles.imageInfo}>
                <span className={styles.uid}>UID: {latestImage.uid}</span>
                <span className={styles.filename}>{latestImage.filename}</span>
              </div>
            </div>
          </div>

          {/* Main Prompt Section */}
          <div className={styles.section}>
            <textarea
              id="mainPrompt"
              value={mainPrompt}
              onChange={(e) => setMainPrompt(e.target.value)}
              placeholder="Overall transformation description (e.g., 'Create a cyberpunk art style')..."
              className={styles.textarea}
              rows={2}
              disabled={submitting}
            />
            <div className={styles.characterCount}>
              {mainPrompt.length}/500 characters
              {mainPrompt.length > 500 && <span className={styles.warning}> (exceeds recommended limit)</span>}
            </div>
          </div>


          {/* Reference Images Section */}
          <div className={styles.section}>
            <h3>Reference Images (max 3)</h3>
            <p className={styles.description}>
              Upload images and provide specific prompts for how each should influence the transformation.
            </p>

            <div className={styles.referenceGrid}>
              {[0, 1, 2].map((index) => (
                <div key={index} className={styles.referenceSlot}>
                  <div className={styles.uploadArea}>
                    {referenceImages[index] ? (
                      <div className={styles.uploadedImage}>
                        <img
                          src={referenceImages[index].preview}
                          alt={`Reference ${index + 1}`}
                          className={styles.referencePreview}
                        />
                        {/* No uploading state - upload happens on submit */}
                        <button
                          className={styles.removeButton}
                          onClick={() => removeReferenceImage(index)}
                          disabled={submitting}
                        >
                          ×
                        </button>
                      </div>
                    ) : (
                      <div
                        className={styles.uploadPlaceholder}
                        onClick={() => fileInputRefs.current[index]?.click()}
                      >
                        <span className={styles.uploadIcon}>+</span>
                        <span>Upload Image</span>
                      </div>
                    )}

                    <input
                      ref={el => fileInputRefs.current[index] = el}
                      type="file"
                      accept="image/*"
                      onChange={(e) => handleFileUpload(index, e.target.files?.[0] || null)}
                      style={{ display: 'none' }}
                      disabled={submitting}
                    />
                  </div>

                  {referenceImages[index] && (
                    <div className={styles.referencePromptContainer}>
                      <label className={styles.referencePromptLabel}>
                        Prompt for Reference {index + 1}:
                      </label>
                      <textarea
                        value={referencePrompts[index] || ''}
                        onChange={(e) => handleReferencePromptChange(index, e.target.value)}
                        placeholder={`How should this reference image influence the transformation? (e.g., "Apply the cyberpunk neon lighting style")`}
                        className={styles.referencePromptTextarea}
                        rows={2}
                        disabled={submitting}
                      />
                      <div className={styles.characterCount}>
                        {(referencePrompts[index] || '').length}/200 characters
                        {(referencePrompts[index] || '').length > 200 && (
                          <span className={styles.warning}> (exceeds recommended limit)</span>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

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
            disabled={
              submitting ||
              (!mainPrompt.trim() && referencePrompts.every(p => !p.trim()))
            }
          >
            {submitting ? 'Uploading & Processing...' : 'Transform Image'}
          </button>
        </div>
      </div>
    </div>
  );
}