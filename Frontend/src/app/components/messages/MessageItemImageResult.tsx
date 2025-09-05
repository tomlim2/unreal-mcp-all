'use client';

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
  
  // If it's a relative URL starting with /api/screenshot/, make it absolute
  if (imageUrl.startsWith('/api/screenshot/')) {
    const httpBridgePort = process.env.NEXT_PUBLIC_HTTP_BRIDGE_PORT || '8080';
    return `http://localhost:${httpBridgePort}${imageUrl}`;
  }
  
  // Otherwise return as-is
  return imageUrl;
}

export default function MessageItemImageResult({ result, resultIndex }: MessageItemImageResultProps) {
  if (result.success) {
    return (
      <div>
        {result.result?.image_url && (
          <div className={styles.screenshotContainer}>
            <img 
              src={getFullImageUrl(result.result.image_url)} 
              alt="Screenshot" 
              className={styles.screenshot}
              onError={(e) => {
                const fullUrl = getFullImageUrl(result.result?.image_url || '');
                console.error('Failed to load screenshot:', fullUrl);
                console.log('Screenshot API called for job:', result.result?.image_url?.split('/').pop());
                e.currentTarget.style.display = 'none';
              }}
            />
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