"use client";

import { useState } from "react";
import styles from "./MessageItem.module.css";

interface VideoResultData {
  video?: {
    url: string;
    metadata?: {
      duration?: { display?: string; seconds?: number };
      generation?: { prompt?: string; resolution?: string; aspect_ratio?: string };
      file_size?: { display?: string };
    };
  };
  video_url?: string;
  cost?: { display?: string; value?: number };
  processing?: { model?: string };
  prompt?: string;
}

interface MessageItemVideoResultProps {
  result: {
    command: string;
    success: boolean;
    result?: VideoResultData;
    error?: string;
  };
  resultIndex: number;
}

function getFullVideoUrl(videoUrl: string): string {
  // If it's already an absolute URL, return as-is
  if (videoUrl.startsWith("http://") || videoUrl.startsWith("https://")) {
    return videoUrl;
  }

  // If it's a video file URL, use Next.js proxy to avoid CORS issues
  if (videoUrl.startsWith("/api/video-file/")) {
    const filename = videoUrl.replace("/api/video-file/", "");
    const proxyUrl = `/api/video/${filename}`;
    console.log("Using Next.js proxy URL for video filename:", proxyUrl);
    return proxyUrl;
  }

  // Direct video URLs
  if (videoUrl.startsWith("/api/video/")) {
    const httpBridgePort = process.env.NEXT_PUBLIC_HTTP_BRIDGE_PORT || "8080";
    const fullUrl = `http://localhost:${httpBridgePort}${videoUrl}`;
    console.log("Generated direct video URL:", fullUrl);
    return fullUrl;
  }

  // Otherwise return as-is
  return videoUrl;
}

export default function MessageItemVideoResult({
  result,
}: MessageItemVideoResultProps) {
  const [videoLoadError, setVideoLoadError] = useState(false);

  if (result.success) {
    const resultData = result.result;

    // Check for new hierarchical schema (video.url)
    const hasNewVideoUrl = resultData?.video?.url && typeof resultData.video.url === "string";

    // Check for legacy schema (video_url)
    const hasLegacyVideoUrl = resultData?.video_url && typeof resultData.video_url === "string";

    if (!hasNewVideoUrl && !hasLegacyVideoUrl) {
      return <div></div>; // Return empty div if no video
    }

    // Get video URL from either new hierarchical or legacy format
    const videoUrl = resultData?.video?.url || resultData?.video_url;

    // Get video metadata
    const videoMetadata = resultData?.video?.metadata;
    const duration = videoMetadata?.duration?.display || `${videoMetadata?.duration?.seconds || 8}s`;
    const prompt = videoMetadata?.generation?.prompt || resultData?.prompt;
    const cost = resultData?.cost?.display || `$${resultData?.cost?.value?.toFixed(3) || '6.000'}`;
    const model = resultData?.processing?.model || 'veo-3.0-generate-001';
    const fileSize = videoMetadata?.file_size?.display || 'Unknown size';
    const resolution = videoMetadata?.generation?.resolution || '720p';
    const aspectRatio = videoMetadata?.generation?.aspect_ratio || '16:9';

    return (
      <div className={styles.screenshotContainer}>
        {!videoLoadError ? (
          <>
            <video
              src={getFullVideoUrl(videoUrl)}
              controls
              preload="metadata"
              className={styles.screenshot} // Reuse screenshot styling for consistency
              style={{ maxWidth: '100%', height: 'auto' }}
              onError={(e) => {
                const fullUrl = getFullVideoUrl(videoUrl);
                const filename = videoUrl.split("/").pop();

                // Only log in development, reduce console noise in production
                if (process.env.NODE_ENV === "development") {
                  console.warn("Video not available:", filename);
                  console.debug("Full URL attempted:", fullUrl);
                }

                setVideoLoadError(true);
                e.preventDefault();
              }}
            >
              Your browser does not support the video tag.
            </video>

            {/* Display UID and filename only */}
            <div className={styles.transformationDetails}>
              <small className={styles.styleInfo}>
                {resultData?.uids?.video && `${resultData.uids.video}`}
                {resultData?.uids?.video && resultData?.filename && ` | `}
                {resultData?.filename && `File: ${resultData.filename}`}
              </small>
            </div>
          </>
        ) : (
          <div className={styles.screenshotError}>
            <div className={styles.errorText}>
              <small>
                The video file &quot;
                {videoUrl.split("/").pop()}
                &quot; could not be loaded
              </small>
              <br />
              <button
                className={styles.retryButton}
                onClick={() => {
                  setVideoLoadError(false);
                }}
                title="Try loading the video again"
              >
                Retry
              </button>
            </div>
          </div>
        )}
      </div>
    );
  } else {
    // Only show error message for video-related commands
    const videoRelatedCommands = ['generate_video_from_image', 'generate_video', 'edit_video'];
    if (videoRelatedCommands.includes(result.command)) {
      return <div className={styles.errorMessage}>{result.error}</div>;
    }
    return null; // Let ExecutionResults handle non-video errors
  }
}