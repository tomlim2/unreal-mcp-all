'use client';

import styles from './MessageItem.module.css';
import MessageItemImageResult from './MessageItemImageResult';
import MessageItemVideoResult from './MessageItemVideoResult';
import MessageItem3DResult from './MessageItem3DResult';

interface ExecutionResultData {
  command: string;
  success: boolean;
  result?: unknown;
  error?: string;
  error_code?: string;
  error_details?: Record<string, unknown>;
  suggestion?: string;
  category?: string;
}

interface ExecutionResultsProps {
  executionResults?: ExecutionResultData[];
  excludeImages?: boolean;
  excludeVideos?: boolean;
}

export default function ExecutionResults({ executionResults, excludeImages = false, excludeVideos = false }: ExecutionResultsProps) {
  if (!executionResults || executionResults.length === 0) {
    return null;
  }

  // Filter results based on excludeImages and excludeVideos props
  const filteredResults = executionResults.filter(result => {
    if (!result.result || typeof result.result !== 'object' || result.result === null) {
      return true; // Keep non-object results
    }

    const resultData = result.result as Record<string, unknown>;

    // Check for image URLs safely
    const imageUnknown = (resultData && 'image' in resultData) ? (resultData['image'] as unknown) : undefined;
    const newImageUrlUnknown = (imageUnknown && typeof imageUnknown === 'object' && imageUnknown !== null)
      ? (imageUnknown as Record<string, unknown>)['url']
      : undefined;
    const legacyImageUrlUnknown = (resultData && 'image_url' in resultData)
      ? (resultData['image_url'] as unknown)
      : undefined;
    const hasImageUrl = (typeof newImageUrlUnknown === 'string') || (typeof legacyImageUrlUnknown === 'string');

    // Check for video URLs safely
    const videoUnknown = (resultData && 'video' in resultData) ? (resultData['video'] as unknown) : undefined;
    const newVideoUrlUnknown = (videoUnknown && typeof videoUnknown === 'object' && videoUnknown !== null)
      ? (videoUnknown as Record<string, unknown>)['url']
      : undefined;
    const legacyVideoUrlUnknown = (resultData && 'video_url' in resultData)
      ? (resultData['video_url'] as unknown)
      : undefined;
    const hasVideoUrl = (typeof newVideoUrlUnknown === 'string') || (typeof legacyVideoUrlUnknown === 'string');

    // Apply filters
    if (excludeImages && hasImageUrl) {
      return false;
    }

    if (excludeVideos && hasVideoUrl) {
      return false;
    }

    return true;
  });

  if (filteredResults.length === 0) {
    return null;
  }

  return (
    <div className={styles.results}>
      {filteredResults.map((result, resultIndex) => {
        const resultData = result.result as Record<string, unknown> | undefined;

        // Check if result has image or video
        const imageUnknown = resultData && 'image' in resultData ? (resultData['image'] as unknown) : undefined;
        const newImageUrlUnknown = (imageUnknown && typeof imageUnknown === 'object' && imageUnknown !== null)
          ? (imageUnknown as Record<string, unknown>)['url']
          : undefined;
        const legacyImageUrlUnknown = resultData && 'image_url' in resultData
          ? (resultData['image_url'] as unknown)
          : undefined;
        const hasImageUrl = (typeof newImageUrlUnknown === 'string') || (typeof legacyImageUrlUnknown === 'string');

        const videoUnknown = resultData && 'video' in resultData ? (resultData['video'] as unknown) : undefined;
        const newVideoUrlUnknown = (videoUnknown && typeof videoUnknown === 'object' && videoUnknown !== null)
          ? (videoUnknown as Record<string, unknown>)['url']
          : undefined;
        const legacyVideoUrlUnknown = resultData && 'video_url' in resultData
          ? (resultData['video_url'] as unknown)
          : undefined;
        const hasVideoUrl = (typeof newVideoUrlUnknown === 'string') || (typeof legacyVideoUrlUnknown === 'string');

        const hasMedia = hasImageUrl || hasVideoUrl;

        // For successful commands with media, only show the media
        if (result.success && hasMedia) {
          return (
            <div key={resultIndex}>
              <MessageItemImageResult result={result} resultIndex={resultIndex} />
              <MessageItemVideoResult result={result} resultIndex={resultIndex} />
              <MessageItem3DResult result={result} resultIndex={resultIndex} />
            </div>
          );
        }

        return (
          <div key={resultIndex} className={`${styles.result} ${result.success ? styles.success : styles.failure}`}>
            <div className={styles.resultHeader}>
              <div className={`${styles.statusCircle} ${result.success ? styles.successCircle : styles.failureCircle}`}></div>
              <span className={styles.commandName}>{result.command}</span>
            </div>

            {/* Message display (success only - errors shown in debug panel) */}
            {result.success && resultData?.message && (
              <div className={styles.successMessage}>
                {resultData.message as string}
              </div>
            )}

            <MessageItemImageResult result={result} resultIndex={resultIndex} />
            <MessageItemVideoResult result={result} resultIndex={resultIndex} />
            <MessageItem3DResult result={result} resultIndex={resultIndex} />
          </div>
        );
      })}
    </div>
  );
}