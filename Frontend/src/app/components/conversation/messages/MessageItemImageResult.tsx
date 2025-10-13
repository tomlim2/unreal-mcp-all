"use client";

import { useState } from "react";
import Image from "next/image";
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

  // Support for screenshot URLs (both /api/screenshot/ and /api/screenshot-file/)
  if (imageUrl.startsWith("/api/screenshot/") || imageUrl.startsWith("/api/screenshot-file/")) {
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
  resultIndex: _resultIndex,
}: MessageItemImageResultProps) {
  const [imageLoadError, setImageLoadError] = useState(false);

  if (result.success) {
    // Narrow result payload to expected image result shape
    interface ResultPayload {
      image?: { url?: string; metadata?: { style?: { prompt?: string } } };
      image_url?: string;
      style_prompt?: string;
      intensity?: unknown;
    }
    const resultData = (result.result ?? {}) as ResultPayload;
    
    // Check for new hierarchical schema (image.url)
    const hasNewImageUrl = resultData?.image?.url && typeof resultData.image.url === "string";
    
    // Check for legacy schema (image_url)
    const hasLegacyImageUrl = resultData?.image_url && typeof resultData.image_url === "string";
    
    if (!hasNewImageUrl && !hasLegacyImageUrl) {
      return <div></div>; // Return empty div if no image
    }

    // Get image URL from either new hierarchical or legacy format
  const imageUrl = resultData.image?.url || resultData.image_url;
    
    // Check if this is a styled image result (new hierarchical or legacy)
    const isStyledImage = resultData?.image?.metadata?.style?.prompt || resultData?.style_prompt || resultData?.intensity;

    return (
      <div className={styles.screenshotContainer}>
        {!imageLoadError ? (
          <>
            <Image
              src={getFullImageUrl(imageUrl as string)}
              alt={isStyledImage ? "Styled Screenshot" : "Screenshot"}
              className={styles.screenshot}
              width={1280}
              height={720}
              unoptimized
              onError={() => {
                const fullUrl = getFullImageUrl(imageUrl as string);
                const filename = (imageUrl as string).split("/").pop();

                if (process.env.NODE_ENV === "development") {
                  console.warn("Screenshot not available:", filename);
                  console.debug("Full URL attempted:", fullUrl);
                }

                setImageLoadError(true);
              }}
            />
          </>
        ) : (
          <div className={styles.screenshotError}>
            <div className={styles.errorText}>
			  <small>
                The image file &quot;
                {(imageUrl ? imageUrl.split("/").pop() : "unknown")}
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
    // Error messages are handled by ExecutionResults component
    return null;
  }
}
