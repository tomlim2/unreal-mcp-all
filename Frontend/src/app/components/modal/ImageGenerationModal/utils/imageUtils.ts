/**
 * Image utility functions
 */

import { DEFAULT_HTTP_BRIDGE_PORT, MAX_FILE_SIZE } from './constants';

/**
 * Transform image URL to full URL with correct host/port
 */
export function getFullImageUrl(imageUrl: string): string {
  // If it's already an absolute URL, return as-is
  if (imageUrl.startsWith("http://") || imageUrl.startsWith("https://")) {
    return imageUrl;
  }

  // Support for screenshot URLs (both /api/screenshot/ and /api/screenshot-file/)
  if (imageUrl.startsWith("/api/screenshot/") || imageUrl.startsWith("/api/screenshot-file/")) {
    const httpBridgePort = process.env.NEXT_PUBLIC_HTTP_BRIDGE_PORT || DEFAULT_HTTP_BRIDGE_PORT;
    const fullUrl = `http://localhost:${httpBridgePort}${imageUrl}`;
    console.log("Generated direct URL:", fullUrl);
    return fullUrl;
  }

  // Otherwise return as-is
  return imageUrl;
}

/**
 * Convert file to base64 data URI
 */
export async function fileToDataUri(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      resolve(reader.result as string); // Returns "data:image/png;base64,..."
    };
    reader.onerror = () => reject(new Error('Failed to read file'));
    reader.readAsDataURL(file);
  });
}

/**
 * Validate image file
 */
export function validateImageFile(file: File): { valid: boolean; error?: string } {
  // Validate file type
  if (!file.type.startsWith('image/')) {
    return { valid: false, error: 'Please select an image file' };
  }

  // Validate file size
  if (file.size > MAX_FILE_SIZE) {
    return { valid: false, error: 'Image must be smaller than 10MB' };
  }

  return { valid: true };
}

/**
 * Create object URL for image preview
 */
export function createPreviewUrl(file: File): string {
  return URL.createObjectURL(file);
}

/**
 * Revoke object URL to free memory
 */
export function revokePreviewUrl(url: string): void {
  URL.revokeObjectURL(url);
}
