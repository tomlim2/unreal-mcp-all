/**
 * Hook for loading session image data from Zustand cache
 */

import { useState, useEffect } from 'react';
import { useSessionImagesStore } from '../../../../stores/sessionImagesStore';
import { LatestImageInfo, SessionImageInfo } from '../types';
import { getFullImageUrl } from '../utils/imageUtils';

export function useSessionImageData(sessionId: string) {
  const { getSessionImages, getLatestImage } = useSessionImagesStore();

  const [latestImage, setLatestImage] = useState<LatestImageInfo | null>(null);
  const [sessionImages, setSessionImages] = useState<SessionImageInfo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // If no session (first page), skip cache loading
    if (!sessionId || sessionId === '') {
      console.log('Modal: No session ID - first page mode, skipping cache');
      setLatestImage({ uid: null, filename: null, thumbnail_url: null, available: false });
      setSessionImages([]);
      setLoading(false);
      return;
    }

    // Get data from cache
    const cachedImages = getSessionImages(sessionId);
    const cachedLatest = getLatestImage(sessionId);

    if (cachedImages && cachedLatest) {
      // Use cached data
      console.log(`Modal: Using cached data for session ${sessionId}`);
      setSessionImages(cachedImages);
      setLatestImage(cachedLatest);
    } else {
      // No cache available - SessionProvider should have loaded this
      console.warn(`Modal: No cached data for session ${sessionId}`);
      setLatestImage({ uid: null, filename: null, thumbnail_url: null, available: false });
      setSessionImages([]);
    }

    setLoading(false);
  }, [sessionId, getSessionImages, getLatestImage]);

  return { latestImage, sessionImages, loading };
}
