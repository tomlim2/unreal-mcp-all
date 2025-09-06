'use client';

import { useState } from 'react';
import styles from './MessageItem.module.css';

interface MessageItemImageResultProps {
  result: {
    command: string;
    success: boolean;
    result?: Record<string, any> & {
      image_url?: string;
    };
    error?: string;
  };
  resultIndex: number;
}

function getFullImageUrl(imageUrl: string): string {
  // If it's already an absolute URL, return as-is
  if (imageUrl.startsWith('http://') || imageUrl.startsWith('https://')) {
    return imageUrl;
  }
  
  // If it's a screenshot file URL, use Next.js proxy to avoid CORS issues
  if (imageUrl.startsWith('/api/screenshot-file/')) {
    const filename = imageUrl.replace('/api/screenshot-file/', '');
    const proxyUrl = `/api/screenshot/${filename}`;
    console.log('Using Next.js proxy URL for filename:', proxyUrl);
    return proxyUrl;
  }
  
  // Legacy support for old screenshot URLs
  if (imageUrl.startsWith('/api/screenshot/')) {
    const httpBridgePort = process.env.NEXT_PUBLIC_HTTP_BRIDGE_PORT || '8080';
    const fullUrl = `http://localhost:${httpBridgePort}${imageUrl}`;
    console.log('Generated direct URL:', fullUrl);
    return fullUrl;
  }
  
  // Otherwise return as-is
  return imageUrl;
}

export default function MessageItemImageResult({ result, resultIndex }: MessageItemImageResultProps) {
  const [imageLoadError, setImageLoadError] = useState(false);

  if (result.success) {
    return (
      <div>
        {result.result?.image_url && (
          <div className={styles.screenshotContainer}>
            {!imageLoadError ? (
              <img 
                src={getFullImageUrl(result.result.image_url)} 
                alt="Screenshot" 
                className={styles.screenshot}
                onError={(e) => {
                  const fullUrl = getFullImageUrl(result.result?.image_url || '');
                  const filename = result.result?.image_url?.split('/').pop();
                  
                  // Only log in development, reduce console noise in production
                  if (process.env.NODE_ENV === 'development') {
                    console.warn('Screenshot not available:', filename);
                    console.debug('Full URL attempted:', fullUrl);
                  }
                  
                  setImageLoadError(true);
                  
                  // Prevent default browser error handling to reduce console noise
                  e.preventDefault();
                }}
              />
            ) : (
              <div className={styles.screenshotError}>
                <div className={styles.errorText}>
                  <strong>Screenshot not available</strong>
                  <br />
                  <small>The image file "{result.result.image_url?.split('/').pop()}" could not be loaded.</small>
                  <br />
                  <button 
                    className={styles.retryButton}
                    onClick={() => setImageLoadError(false)}
                    title="Try loading the image again"
                  >
                    Retry
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    );
  } else {
    return (
      <div className={styles.errorMessage}>{result.error}</div>
    );
  }
}