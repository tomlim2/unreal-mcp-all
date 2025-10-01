/**
 * Image Processing Types
 *
 * Copyright Policy:
 * - User uploads are processed client-side only
 * - Images sent to backend are base64 encoded
 * - Backend stores ONLY generated results
 */

export interface ImageUpload {
  file: File;
  preview: string;
  purpose?: 'main' | 'reference' | 'style';
}

export interface ImageData {
  data: string;        // base64 Data URI
  mime_type: string;
}

export interface ProcessedImage {
  data: string;        // base64 Data URI
  mime_type: string;
  size_kb: number;
  width?: number;
  height?: number;
}

export interface ImageValidationOptions {
  maxSizeMB?: number;
  allowedTypes?: string[];
  requireDimensions?: boolean;
}

export interface ImageValidationResult {
  valid: boolean;
  error?: string;
  warnings?: string[];
}
