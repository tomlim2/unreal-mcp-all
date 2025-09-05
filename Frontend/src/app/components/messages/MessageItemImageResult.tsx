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

export default function MessageItemImageResult({ result, resultIndex }: MessageItemImageResultProps) {
  if (result.success) {
    return (
      <div>
        <pre className={styles.resultData}>
          {JSON.stringify(result.result, null, 2)}
        </pre>
        {result.result?.image_url && (
          <div className={styles.screenshotContainer}>
            <img 
              src={result.result.image_url} 
              alt="Screenshot" 
              className={styles.screenshot}
              onError={(e) => {
                console.error('Failed to load screenshot:', result.result?.image_url);
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