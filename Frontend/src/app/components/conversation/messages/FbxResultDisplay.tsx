'use client';

import styles from './MessageItem.module.css';
import ErrorDisplay from './ErrorDisplay';

interface FbxResultDisplayProps {
  success: boolean;
  fbxUid?: string;
  objUid?: string;
  conversionMessage?: string;
  errorMessage?: string;
  errorCode?: string;
  category?: string;
  errorDetails?: Record<string, unknown>;
  suggestion?: string;
}

export default function FbxResultDisplay({
  success,
  fbxUid,
  objUid,
  conversionMessage,
  errorMessage,
  errorCode,
  category,
  errorDetails,
  suggestion
}: FbxResultDisplayProps) {
  if (success && fbxUid) {
    return (
      <div className={styles.resultContent}>
        <div className={styles.resultMessage}>
          <strong>FBX UID:</strong> {fbxUid}
        </div>
        {objUid && (
          <div className={styles.resultDetail}>
            <strong>Source OBJ UID:</strong> {objUid}
          </div>
        )}
        {conversionMessage && (
          <div className={styles.resultDetail}>
            {conversionMessage}
          </div>
        )}
      </div>
    );
  }

  if (!success && errorMessage) {
    return (
      <>
        <ErrorDisplay
          errorMessage={errorMessage}
          errorCode={errorCode}
          category={category}
          errorDetails={errorDetails}
          suggestion={suggestion}
        />
        {objUid && (
          <div className={styles.resultDetail}>
            <strong>Failed OBJ UID:</strong> {objUid}
          </div>
        )}
      </>
    );
  }

  return null;
}
