'use client';

import styles from './MessageItem.module.css';
import MessageItemImageResult from './MessageItemImageResult';
import MessageItemVideoResult from './MessageItemVideoResult';

interface ExecutionResultData {
  command: string;
  success: boolean;
  result?: unknown;
  error?: string;
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

    // Check for image URLs
    const hasNewImageUrl = resultData?.image?.url;
    const hasLegacyImageUrl = resultData?.image_url;
    const hasImageUrl = hasNewImageUrl || hasLegacyImageUrl;

    // Check for video URLs
    const hasNewVideoUrl = resultData?.video?.url;
    const hasLegacyVideoUrl = resultData?.video_url;
    const hasVideoUrl = hasNewVideoUrl || hasLegacyVideoUrl;

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
      <strong>Unreal Engine Execution Results:</strong>
      {filteredResults.map((result, resultIndex) => {
        const resultData = result.result as Record<string, unknown> | undefined;

        // Check for Roblox FBX conversion result
        const isFbxConversion = result.command === 'convert_roblox_obj_to_fbx';
        const fbxUid = resultData?.fbx_uid as string | undefined;
        const objUid = resultData?.obj_uid as string | undefined;
        const conversionMessage = resultData?.message as string | undefined;

        // Check for error details
        const errorMessage = result.error || (resultData?.error as string | undefined);
        const errorSuggestion = resultData?.suggestion as string | undefined;

        return (
          <div key={resultIndex} className={`${styles.result} ${result.success ? styles.success : styles.failure}`}>
            <div className={styles.resultHeader}>
              <div className={`${styles.statusCircle} ${result.success ? styles.successCircle : styles.failureCircle}`}></div>
              <span className={styles.commandName}>{result.command}</span>
            </div>

            {/* Roblox FBX Conversion - Success */}
            {isFbxConversion && result.success && fbxUid && (
              <div className={styles.resultContent}>
                <div className={styles.resultMessage}>
                  ✅ <strong>FBX UID:</strong> {fbxUid}
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
            )}

            {/* Roblox FBX Conversion - Error */}
            {isFbxConversion && !result.success && errorMessage && (
              <div className={styles.resultContent}>
                <div className={styles.errorMessage}>
                  ❌ <strong>Error:</strong> {errorMessage}
                </div>
                {errorSuggestion && (
                  <div className={styles.errorSuggestion}>
                    💡 <strong>Suggestion:</strong> {errorSuggestion}
                  </div>
                )}
                {objUid && (
                  <div className={styles.resultDetail}>
                    <strong>Failed OBJ UID:</strong> {objUid}
                  </div>
                )}
              </div>
            )}

            <MessageItemImageResult result={result} resultIndex={resultIndex} />
            <MessageItemVideoResult result={result} resultIndex={resultIndex} />
          </div>
        );
      })}
    </div>
  );
}