/**
 * Local types for Reference Images Modal
 */

export interface LatestImageInfo {
  uid: string | null;
  filename: string | null;
  thumbnail_url: string | null;
  available: boolean;
}

export interface SessionImageInfo {
  uid: string;
  url: string;
  thumbnail_url: string;
  filename: string;
  timestamp: string;
  command: string;
}

export interface SelectedImageUpload {
  type: 'upload';
  preview: string;
}

export interface SelectedImageSession {
  type: 'session';
  url: string;
  uid: string;
  filename: string;
}

export type SelectedImage = SelectedImageUpload | SelectedImageSession | null;
