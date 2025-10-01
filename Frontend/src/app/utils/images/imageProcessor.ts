/**
 * Image Processing Utilities
 *
 * Copyright Policy:
 * - Images processed client-side and sent as base64
 * - No storage on client side (only preview URLs)
 * - Backend handles storage decisions
 */

import { ImageData, ProcessedImage, ImageUpload } from './types';
import { ImageValidator } from './imageValidator';

export class ImageProcessor {
  /**
   * Convert File to base64 Data URI
   */
  static async fileToDataUri(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();

      reader.onload = () => {
        resolve(reader.result as string);
      };

      reader.onerror = () => {
        reject(new Error('Failed to read file'));
      };

      reader.readAsDataURL(file);
    });
  }

  /**
   * Convert File to ImageData object
   */
  static async fileToImageData(file: File): Promise<ImageData> {
    const dataUri = await this.fileToDataUri(file);

    return {
      data: dataUri,
      mime_type: file.type
    };
  }

  /**
   * Process uploaded file with validation
   */
  static async processUpload(file: File): Promise<ProcessedImage> {
    // Validate
    const validation = ImageValidator.validateFile(file);
    if (!validation.valid) {
      throw new Error(validation.error || 'Validation failed');
    }

    // Convert to base64
    const dataUri = await this.fileToDataUri(file);
    const sizeKB = file.size / 1024;

    // Try to get dimensions (optional)
    let width: number | undefined;
    let height: number | undefined;

    try {
      const dimensions = await this.getImageDimensions(dataUri);
      width = dimensions.width;
      height = dimensions.height;
    } catch (error) {
      console.warn('Could not get image dimensions:', error);
    }

    return {
      data: dataUri,
      mime_type: file.type,
      size_kb: Math.round(sizeKB),
      width,
      height
    };
  }

  /**
   * Process multiple uploads
   */
  static async processUploads(files: File[]): Promise<ProcessedImage[]> {
    return Promise.all(
      files.map(file => this.processUpload(file))
    );
  }

  /**
   * Get image dimensions from Data URI
   */
  static getImageDimensions(dataUri: string): Promise<{ width: number; height: number }> {
    return new Promise((resolve, reject) => {
      const img = new Image();

      img.onload = () => {
        resolve({
          width: img.width,
          height: img.height
        });
      };

      img.onerror = () => {
        reject(new Error('Failed to load image'));
      };

      img.src = dataUri;
    });
  }

  /**
   * Create preview URL from File
   */
  static createPreviewUrl(file: File): string {
    return URL.createObjectURL(file);
  }

  /**
   * Cleanup preview URL
   */
  static revokePreviewUrl(url: string): void {
    URL.revokeObjectURL(url);
  }

  /**
   * Cleanup multiple preview URLs
   */
  static revokePreviewUrls(urls: string[]): void {
    urls.forEach(url => URL.revokeObjectURL(url));
  }

  /**
   * Handle file upload with validation and preview
   */
  static async handleFileUpload(
    file: File,
    purpose: 'main' | 'reference' | 'style' = 'reference'
  ): Promise<ImageUpload> {
    // Validate
    const validation = ImageValidator.validateFile(file);
    if (!validation.valid) {
      throw new Error(validation.error || 'Validation failed');
    }

    // Show warnings
    if (validation.warnings && validation.warnings.length > 0) {
      console.warn('Image upload warnings:', validation.warnings);
    }

    // Create preview
    const preview = this.createPreviewUrl(file);

    return {
      file,
      preview,
      purpose
    };
  }
}
