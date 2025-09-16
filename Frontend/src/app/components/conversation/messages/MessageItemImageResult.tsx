"use client";

import { useState } from "react";
import styles from "./MessageItem.module.css";

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
  if (imageUrl.startsWith("http://") || imageUrl.startsWith("https://")) {
    return imageUrl;
  }

  // If it's a screenshot file URL, use Next.js proxy to avoid CORS issues
  if (imageUrl.startsWith("/api/screenshot-file/")) {
    const filename = imageUrl.replace("/api/screenshot-file/", "");
    const proxyUrl = `/api/screenshot/${filename}`;
    console.log("Using Next.js proxy URL for filename:", proxyUrl);
    return proxyUrl;
  }

  // Legacy support for old screenshot URLs
  if (imageUrl.startsWith("/api/screenshot/")) {
    const httpBridgePort = process.env.NEXT_PUBLIC_HTTP_BRIDGE_PORT || "8080";
    const fullUrl = `http://localhost:${httpBridgePort}${imageUrl}`;
    console.log("Generated direct URL:", fullUrl);
    return fullUrl;
  }

  // Otherwise return as-is
  return imageUrl;
}

export default function MessageItemImageResult({
  result,
  resultIndex,
}: MessageItemImageResultProps) {
  const [imageLoadError, setImageLoadError] = useState(false);

  if (result.success) {
    const resultData = result.result as any;
    
    // Check for new hierarchical schema (image.url)
    const hasNewImageUrl = resultData?.image?.url && typeof resultData.image.url === "string";
    
    // Check for legacy schema (image_url)
    const hasLegacyImageUrl = resultData?.image_url && typeof resultData.image_url === "string";
    
    if (!hasNewImageUrl && !hasLegacyImageUrl) {
      return <div></div>; // Return empty div if no image
    }

    // Get image URL from either new hierarchical or legacy format
    const imageUrl = resultData?.image?.url || resultData?.image_url;
    
    // Check if this is a styled image result (new hierarchical or legacy)
    const isStyledImage = resultData?.image?.metadata?.style?.prompt || resultData?.style_prompt || resultData?.intensity;

    return (
      <div className={styles.screenshotContainer}>
        {!imageLoadError ? (
          <>
            <img
              src={getFullImageUrl(imageUrl)}
              alt={isStyledImage ? "Styled Screenshot" : "Screenshot"}
              className={styles.screenshot}
              onError={(e) => {
                const fullUrl = getFullImageUrl(imageUrl);
                const filename = imageUrl.split("/").pop();

                // Only log in development, reduce console noise in production
                if (process.env.NODE_ENV === "development") {
                  console.warn("Screenshot not available:", filename);
                  console.debug("Full URL attempted:", fullUrl);
                }

                setImageLoadError(true);
                e.preventDefault();
              }}
            />
            {/* Display transformation details for styled images */}
            {isStyledImage && (
              <div className={styles.transformationDetails}>
                <small className={styles.styleInfo}>
                  Applied: {resultData?.image?.metadata?.style?.prompt || resultData?.style_prompt}
                  {(resultData?.image?.metadata?.style?.intensity || resultData?.intensity) && 
                    ` (intensity: ${resultData?.image?.metadata?.style?.intensity || resultData?.intensity})`}
                </small>
              </div>
            )}
          </>
        ) : (
          <div className={styles.screenshotError}>
            <div className={styles.errorText}>
			  <small>
                The image file &quot;
                {imageUrl.split("/").pop()}
                &quot; could not be loaded
              </small>
			  <br />
              <button
                className={styles.retryButton}
                onClick={() => {
                  setImageLoadError(false);
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
    return <div className={styles.errorMessage}>{result.error}</div>;
  }
}
