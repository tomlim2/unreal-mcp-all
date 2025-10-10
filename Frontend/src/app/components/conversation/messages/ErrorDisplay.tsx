'use client';

import styles from './MessageItem.module.css';

interface ErrorDisplayProps {
  errorMessage: string;
  errorCode?: string;
  category?: string;
  errorDetails?: Record<string, unknown>;
  suggestion?: string;
}

export default function ErrorDisplay({
  errorMessage,
  errorCode,
  category,
  errorDetails,
  suggestion
}: ErrorDisplayProps) {
  return (
    <div className={styles.resultContent}>
      {errorCode && (
        <div className={styles.resultDetail}>
          <strong>Code:</strong> {errorCode}
        </div>
      )}

      {category && (
        <div className={styles.resultDetail}>
          <strong>Category:</strong> {category}
        </div>
      )}

      {errorDetails && Object.keys(errorDetails).length > 0 && (
        <div className={styles.resultDetail}>
          <strong>Details:</strong>
          <pre style={{ marginTop: '4px', fontSize: '0.9em' }}>
            {JSON.stringify(errorDetails, null, 2)}
          </pre>
        </div>
      )}

      {suggestion && (
        <div className={styles.errorSuggestion}>
          <strong>Suggestion:</strong> {suggestion}
        </div>
      )}
    </div>
  );
}
