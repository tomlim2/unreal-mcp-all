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
  const [mainImageUpload, setMainImageUpload] = useState<{ file: File; preview: string } | null>(null);
  const [referenceImages, setReferenceImages] = useState<ReferenceImageUpload[]>([]);
  const [referencePrompts, setReferencePrompts] = useState<string[]>(['', '', '']); // Individual prompts for each reference image

  const fileInputRefs = useRef<(HTMLInputElement | null)[]>([]);
  const mainImageInputRef = useRef<HTMLInputElement | null>(null);
  const imageUrlRef = useRef<string | null>(null);

  // Fetch latest image info - only once on mount
  useEffect(() => {
    async function fetchLatestImage() {
      // Skip fetching if no sessionId (user will upload main image)
      if (!sessionId) {
        setLatestImage({ uid: null, filename: null, thumbnail_url: null, available: false });
        setLoading(false);
        return;
      }

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

  // Handle main image upload
  const handleMainImageUpload = async (file: File | null) => {
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

    // Clean up old preview if exists
    if (mainImageUpload?.preview) {
      URL.revokeObjectURL(mainImageUpload.preview);
    }

    setMainImageUpload({ file, preview });
  };

  // Remove main image upload
  const removeMainImageUpload = () => {
    if (mainImageUpload?.preview) {
      URL.revokeObjectURL(mainImageUpload.preview);
    }
    setMainImageUpload(null);
  };

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

  // Convert file to base64 data URI
  const fileToDataUri = async (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        resolve(reader.result as string); // Returns "data:image/png;base64,..."
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

  // Handle submit - send images directly with transformation request
  const handleSubmit = async () => {
    // Check if we have either a target image UID OR a main image upload
    const hasTargetImage = latestImage?.available && latestImage.uid;
    const hasMainImageUpload = mainImageUpload !== null;

    if (!hasTargetImage && !hasMainImageUpload) {
      alert('Please provide a target image (either upload one or use an existing screenshot)');
      return;
    }

    if (!mainPrompt.trim() && referencePrompts.every(p => !p.trim())) {
      alert('Please enter at least one prompt (main prompt or reference prompts)');
      return;
    }

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

      // Convert all reference images to base64 data URIs
      const referenceImageData = [];

      for (let i = 0; i < referenceImages.length; i++) {
        const refImage = referenceImages[i];
        try {
          const dataUri = await fileToDataUri(refImage.file);
          referenceImageData.push({
            data: dataUri,
            mime_type: refImage.file.type
          });
        } catch (error) {
          console.error(`Failed to convert reference image ${i + 1}:`, error);
          alert(`Failed to process reference image ${i + 1}. Please try again.`);
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
        targetImageUid: hasTargetImage ? latestImage.uid : undefined,
        mainImageData: mainImageData, // NEW: User-uploaded main image
        referenceImageData // NEW: Direct image data (replaces referenceImageUids)
      };

      console.log('ReferenceImagesModal: Submitting data with direct images:', {
        prompt: data.prompt,
        main_prompt: data.main_prompt,
        reference_prompts: data.reference_prompts,
        targetImageUid: data.targetImageUid,
        mainImageData: mainImageData ? 'present' : 'none',
        referenceImageData: data.referenceImageData?.length || 0
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
    if (mainImageUpload?.preview) {
      URL.revokeObjectURL(mainImageUpload.preview);
    }
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

  // Show main image upload UI if no latest image OR user uploaded an image
  const showMainImageUpload = !latestImage?.available || mainImageUpload !== null;

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
            <h3>Target Image (Main Image to Transform)</h3>
            {showMainImageUpload ? (
              <div className={styles.targetImage}>
                {mainImageUpload ? (
                  <div className={styles.uploadedImage}>
                    <img
                      src={mainImageUpload.preview}
                      alt="Main image to transform"
                      className={styles.thumbnail}
                    />
                    <button
                      className={styles.removeButton}
                      onClick={removeMainImageUpload}
                      disabled={submitting}
                    >
                      ×
                    </button>
                  </div>
                ) : (
                  <div
                    className={styles.uploadPlaceholder}
                    onClick={() => mainImageInputRef.current?.click()}
                  >
                    <span className={styles.uploadIcon}>+</span>
                    <span>Upload Main Image to Transform</span>
                  </div>
                )}
                <input
                  ref={mainImageInputRef}
                  type="file"
                  accept="image/*"
                  onChange={(e) => handleMainImageUpload(e.target.files?.[0] || null)}
                  style={{ display: 'none' }}
                  disabled={submitting}
                />
              </div>
            ) : (
              <div className={styles.targetImage}>
                <img
                  src={imageUrlRef.current || getFullImageUrl(latestImage!.thumbnail_url!)}
                  alt={`Image ${latestImage!.uid}`}
                  className={styles.thumbnail}
                />
                <div className={styles.imageInfo}>
                  <span className={styles.uid}>UID: {latestImage!.uid}</span>
                  <span className={styles.filename}>{latestImage!.filename}</span>
                </div>
                <button
                  className={styles.button}
                  onClick={() => mainImageInputRef.current?.click()}
                  disabled={submitting}
                  style={{ marginTop: '8px' }}
                >
                  Upload Different Image Instead
                </button>
                <input
                  ref={mainImageInputRef}
                  type="file"
                  accept="image/*"
                  onChange={(e) => handleMainImageUpload(e.target.files?.[0] || null)}
                  style={{ display: 'none' }}
                  disabled={submitting}
                />
              </div>
            )}
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