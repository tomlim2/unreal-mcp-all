'use client';

import { useState } from 'react';
import styles from './MessageItem.module.css';

interface MessageItemImageResultProps {
  result: {
    command: string;
    success: boolean;
    result?: unknown;
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
  const [imageLoaded, setImageLoaded] = useState(false);

  if (result.success) {
    const hasImageUrl = result.result && 
      typeof result.result === 'object' && 
      result.result !== null &&
      'image_url' in result.result &&
      typeof (result.result as any).image_url === 'string';
      
    if (!hasImageUrl) {
      return <div></div>; // Return empty div if no image
    }
      
    return (
      <div className={styles.screenshotContainer}>
        {!imageLoadError ? (
          <>
            {!imageLoaded && (
              <div style={{
                display: 'flex',
                alignItems: 'center',
                color: '#cccccc',
                fontSize: '0.875rem',
                width: '100%',
                minHeight: '150px'
              }}>
                Loading image...
              </div>
            )}
            <img 
              src={getFullImageUrl((result.result as any).image_url)} 
              alt="Screenshot" 
              className={styles.screenshot}
              style={{ display: imageLoaded ? 'block' : 'none' }}
              onLoad={() => setImageLoaded(true)}
              onError={(e) => {
                const imageUrl = (result.result as any).image_url || '';
                const fullUrl = getFullImageUrl(imageUrl);
                const filename = imageUrl.split('/').pop();
                
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
          </>
        ) : (
          <div className={styles.screenshotError}>
            <div className={styles.errorText}>
              <strong>Screenshot not available</strong>
              <br />
              <small>The image file &quot;{((result.result as any).image_url || '').split('/').pop()}&quot; could not be loaded.</small>
              <br />
              <button 
                className={styles.retryButton}
                onClick={() => {
                  setImageLoadError(false);
                  setImageLoaded(false);
                }}
                title="Try loading the image again"
              >
                Retry
              </button>
            </div>
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