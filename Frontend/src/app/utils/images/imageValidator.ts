/**
 * Image Validation Utilities
 */

import { ImageValidationOptions, ImageValidationResult } from './types';

export class ImageValidator {
  private static DEFAULT_MAX_SIZE_MB = 10;
  private static DEFAULT_ALLOWED_TYPES = ['image/png', 'image/jpeg', 'image/jpg'];

  /**
   * Validate uploaded file
   */
  static validateFile(
    file: File,
    options: ImageValidationOptions = {}
  ): ImageValidationResult {
    const maxSizeMB = options.maxSizeMB || this.DEFAULT_MAX_SIZE_MB;
    const allowedTypes = options.allowedTypes || this.DEFAULT_ALLOWED_TYPES;

    // Check file type
    if (!file.type.startsWith('image/')) {
      return {
        valid: false,
        error: 'File must be an image'
      };
    }

    // Check allowed types
    if (!allowedTypes.includes(file.type)) {
      return {
        valid: false,
        error: `Image type not supported. Allowed: ${allowedTypes.join(', ')}`
      };
    }

    // Check file size
    const sizeMB = file.size / (1024 * 1024);
    if (sizeMB > maxSizeMB) {
      return {
        valid: false,
        error: `Image too large: ${sizeMB.toFixed(2)}MB (max: ${maxSizeMB}MB)`
      };
    }

    // Warnings for large files
    const warnings: string[] = [];
    if (sizeMB > maxSizeMB * 0.8) {
      warnings.push(`Large file size: ${sizeMB.toFixed(2)}MB`);
    }

    return {
      valid: true,
      warnings: warnings.length > 0 ? warnings : undefined
    };
  }

  /**
   * Validate multiple files
   */
  static validateFiles(
    files: File[],
    options: ImageValidationOptions = {}
  ): ImageValidationResult[] {
    return files.map(file => this.validateFile(file, options));
  }
}
