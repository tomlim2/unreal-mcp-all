'use client';

import styles from './MessageItem.module.css';
import MessageItemImageResult from './MessageItemImageResult';
import MessageItemVideoResult from './MessageItemVideoResult';
import ErrorDisplay from './ErrorDisplay';
import FbxResultDisplay from './FbxResultDisplay';

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

            {/* Roblox FBX Conversion */}
            {isFbxConversion && (
              <FbxResultDisplay
                success={result.success}
                fbxUid={fbxUid}
                objUid={objUid}
                conversionMessage={conversionMessage}
                errorMessage={errorMessage}
                errorCode={result.error_code}
                category={result.category}
                errorDetails={result.error_details}
                suggestion={errorSuggestion || result.suggestion}
              />
            )}

            {/* General error display */}
            {!isFbxConversion && !result.success && errorMessage && (
              <ErrorDisplay
                errorMessage={errorMessage}
                errorCode={result.error_code}
                category={result.category}
                errorDetails={result.error_details}
                suggestion={result.suggestion}
              />
            )}

            <MessageItemImageResult result={result} resultIndex={resultIndex} />
            <MessageItemVideoResult result={result} resultIndex={resultIndex} />
          </div>
        );
      })}
    </div>
  );
}