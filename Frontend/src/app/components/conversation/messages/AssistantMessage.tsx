"use client";

import { useState, useEffect, useCallback } from "react";
import styles from "./MessageItem.module.css";
import ExecutionResults from "./ExecutionResults";

interface ExecutionResultData {
  command: string;
  success: boolean;
  result?: unknown;
  error?: string;
}

interface ChatMessage {
  timestamp: string;
  role: "user" | "assistant" | "system";
  content: string;
  commands?: Array<{
    type: string;
    params: Record<string, unknown>;
  }>;
  execution_results?: ExecutionResultData[];
  explanation?: string;
  expectedResult?: string;
  error?: string;
  fallback?: boolean;
  model_used?: string; // Track which model was used for this message
}

interface AssistantMessageProps {
  message: ChatMessage;
  sessionName?: string;
  keyPrefix: string | number;
  sessionId?: string;
  allMessages?: ChatMessage[];
  currentIndex?: number;
}

// Token Analysis Panel Component
function TokenAnalysisPanel({ message }: { message: ChatMessage }) {
  const [tokenInfo, setTokenInfo] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const calculateCosts = (
    tokens: number,
    imageTokens: number,
    modelUsed?: string,
    backendImageCost?: number,
    backendVideoCost?: number
  ) => {
    // Model-specific pricing (as of 2024)
    const MODEL_PRICING = {
      gemini: {
        input: 0.000075 / 1000, // $0.075 per 1M tokens (Gemini-1.5-Flash)
        output: 0.0003 / 1000, // $0.30 per 1M tokens
        name: "Gemini-1.5-Flash",
      },
      "gemini-2": {
        input: 0.000075 / 1000, // $0.075 per 1M tokens (Gemini-2.5-Flash)
        output: 0.0003 / 1000, // $0.30 per 1M tokens
        name: "Gemini-2.5-Flash",
      },
      claude: {
        input: 0.003 / 1000, // $3.00 per 1M tokens (Claude-3-Sonnet)
        output: 0.015 / 1000, // $15.00 per 1M tokens
        name: "Claude-3-Sonnet",
      },
      "claude-3-haiku-20240307": {
        input: 0.00025 / 1000, // $0.25 per 1M tokens (Claude-3-Haiku)
        output: 0.00125 / 1000, // $1.25 per 1M tokens
        name: "Claude-3-Haiku",
      },
    };

    // Image processing pricing (Gemini image generation - 2025 pricing)
    const GEMINI_IMAGE_GENERATION = 0.03 / 1000; // $30.00 per 1M tokens (image generation)

    // Get model pricing, default to gemini-2 if unknown
    const modelKey = modelUsed || "gemini-2";
    const pricing = MODEL_PRICING[modelKey] || MODEL_PRICING["gemini-2"];

    // Estimate input/output split (rough approximation)
    const inputTokens = Math.ceil(tokens * 0.7); // 70% input
    const outputTokens = Math.floor(tokens * 0.3); // 30% output

    const nlpCost = inputTokens * pricing.input + outputTokens * pricing.output;
    // Use backend-provided cost if available, otherwise fall back to frontend calculation
    const imageCost =
      backendImageCost !== undefined && backendImageCost > 0
        ? backendImageCost
        : imageTokens > 0
        ? imageTokens * GEMINI_IMAGE_GENERATION
        : 0;

    // Video generation cost (Veo-3 pricing)
    const videoCost = backendVideoCost || 0;

    return {
      nlp: nlpCost,
      image: imageCost,
      video: videoCost,
      total: nlpCost + imageCost + videoCost,
      modelName: pricing.name,
    };
  };

  const analyzeTokens = async () => {
    setLoading(true);
    try {
      // Estimate tokens from user input
      const userInput = message.content || "";
      const hasNonAscii = /[^\x00-\x7F]/.test(userInput);
      const charCount = userInput.length;
      const estimatedTokens = hasNonAscii
        ? Math.ceil(charCount / 2.5)
        : Math.ceil(charCount / 4);

      // Check if this involved image commands (Nano Banana)
      const imageCommands = (message.commands || []).filter(
        (cmd) => cmd.type === "transform_image_style"
      );
      // Check if this involved video commands (Veo-3)
      const videoCommands = (message.commands || []).filter(
        (cmd) => cmd.type === "generate_video_from_image"
      );

      let imageTokenEstimate = 0;
      let imageMetadata = null;

      if (imageCommands.length > 0) {
        // Look for actual image metadata in execution results
        const imageResults = (message.execution_results || []).find(
          (result) =>
            result.result &&
            typeof result.result === "object" &&
            ((result.result as any).image?.metadata ||
              (result.result as any).cost?.tokens)
        );

        if (imageResults && (imageResults.result as any)) {
          const resultData = imageResults.result as any;

          // Handle hierarchical schema (only supported format)
          if (resultData.image?.metadata) {
            imageMetadata = resultData.image.metadata;
            // Use cost data for token count
            if (resultData.cost?.tokens) {
              imageTokenEstimate = resultData.cost.tokens;
            } else {
              imageTokenEstimate = 900; // Fallback estimate
            }
          } else {
            // Fallback to conservative estimate
            imageTokenEstimate = imageCommands.length * 900;
          }
        } else {
          // Fallback to conservative estimate
          imageTokenEstimate = imageCommands.length * 900;
        }
      }

      // Process video commands (Veo-3)
      let videoMetadata = null;
      let backendVideoCost = 0;

      if (videoCommands.length > 0) {
        // Look for actual video metadata in execution results
        const videoResults = (message.execution_results || []).find(
          (result) =>
            result.result &&
            typeof result.result === "object" &&
            ((result.result as any).video?.metadata ||
              (result.result as any).cost?.value)
        );

        if (videoResults && (videoResults.result as any)) {
          const resultData = videoResults.result as any;

          // Handle hierarchical schema
          if (resultData.video?.metadata) {
            videoMetadata = resultData.video.metadata;
          }

          // Use cost data
          if (resultData.cost?.value) {
            backendVideoCost = resultData.cost.value;
          } else {
            // Fallback: Veo-3 standard cost (8 seconds * $0.75/second)
            backendVideoCost = 6.0;
          }
        } else {
          // Fallback cost for video generation
          backendVideoCost = videoCommands.length * 6.0;
        }
      }

      // Calculate costs with model-specific pricing
      // Use hierarchical schema cost data
      let backendImageCost = 0;

      // Check for cost in hierarchical format
      const imageResults = (message.execution_results || []).find(
        (result) => result.result && typeof result.result === "object"
      );

      if (imageResults) {
        const resultData = imageResults.result as any;

        // Hierarchical format has direct cost value
        if (resultData.cost?.value) {
          backendImageCost = resultData.cost.value;
        }
      }

      const costs = calculateCosts(
        estimatedTokens,
        imageTokenEstimate,
        message.model_used,
        backendImageCost,
        backendVideoCost
      );
      setTokenInfo({
        userInput: {
          characters: charCount,
          estimatedTokens,
          hasNonAscii,
          language: hasNonAscii ? "Non-English" : "English",
        },
        imageProcessing: {
          commandCount: imageCommands.length,
          estimatedTokens: imageTokenEstimate,
          commands: imageCommands.map((cmd) => cmd.type),
          metadata: imageMetadata,
        },
        videoProcessing: {
          commandCount: videoCommands.length,
          commands: videoCommands.map((cmd) => cmd.type),
          metadata: videoMetadata,
          cost: backendVideoCost,
        },
        totalEstimate: estimatedTokens + imageTokenEstimate,
        costs: costs,
      });
    } catch (error) {
      console.error("Token analysis failed:", error);
      setTokenInfo({ error: error.message });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    analyzeTokens();
  }, [message]);

  if (!tokenInfo && !loading) return null;

  return (
    <div className={styles.debugBlock}>
      <div className={styles.debugHeader}>
        <strong>TOKEN ANALYSIS</strong>
        <div className={styles.buttonGroup}>
          <button
            onClick={() => {
              if (!tokenInfo || tokenInfo.error) return;

              let analysisText = "# Token Analysis\n\n";

              // Usage Summary
              analysisText += `## Usage Summary\n`;
              analysisText += `- Total Tokens: ${tokenInfo.totalEstimate.toLocaleString()}\n`;
              analysisText += `- Total Cost: $${tokenInfo.costs.total.toFixed(
                6
              )}\n\n`;

              // Breakdown by Category
              analysisText += `## Breakdown by Category\n`;
              analysisText += `1. **NLP (Text Processing)**\n`;
              analysisText += `   - Tokens: ${tokenInfo.userInput.estimatedTokens}\n`;
              analysisText += `   - Model: ${tokenInfo.costs.modelName}\n`;
              analysisText += `   - Cost: $${tokenInfo.costs.nlp.toFixed(
                6
              )}\n\n`;

              if (tokenInfo.imageProcessing.commandCount > 0) {
                analysisText += `2. **Image (Visual Processing)**\n`;
                analysisText += `   - Tokens: ${tokenInfo.imageProcessing.estimatedTokens.toLocaleString()}\n`;
                analysisText += `   - Service: Nano Banana\n`;
                if (tokenInfo.imageProcessing.metadata) {
                  const meta = tokenInfo.imageProcessing.metadata;
                  // Handle hierarchical format only
                  let sizeInfo = "";
                  if (meta.size) {
                    sizeInfo =
                      meta.size.processed || meta.size.original || "Unknown";
                  }

                  let fileSize = "";
                  if (meta.file_size) {
                    fileSize = meta.file_size.display || "Unknown";
                  }

                  analysisText += `   - Image Details: ${sizeInfo} • ${fileSize}\n`;
                }
                analysisText += `   - Cost: $${tokenInfo.costs.image.toFixed(
                  6
                )}\n\n`;
              }

              if (tokenInfo.videoProcessing.commandCount > 0) {
                analysisText += `3. **Video (Veo-3 Generation)**\n`;
                analysisText += `   - Service: Google Veo-3\n`;
                if (tokenInfo.videoProcessing.metadata) {
                  const meta = tokenInfo.videoProcessing.metadata;
                  const duration = meta.duration?.display || "8s";
                  const resolution = meta.generation?.resolution || "720p";
                  const aspectRatio = meta.generation?.aspect_ratio || "16:9";

                  analysisText += `   - Video Details: ${resolution} (${aspectRatio}) • ${duration}\n`;
                  if (meta.generation?.prompt) {
                    analysisText += `   - Prompt: ${meta.generation.prompt}\n`;
                  }
                }
                analysisText += `   - Cost: $${tokenInfo.costs.video.toFixed(
                  6
                )}\n\n`;
              }

              // High usage warning
              if (tokenInfo.totalEstimate > 800) {
                analysisText += `⚠️ High usage (${tokenInfo.totalEstimate} tokens) - may consume daily quota quickly\n\n`;
              }

              navigator.clipboard.writeText(analysisText);
            }}
            className={styles.copyButton}
            disabled={!tokenInfo || tokenInfo.error}
          >
            Copy Analysis
          </button>
        </div>
      </div>

      {tokenInfo?.error ? (
        <div className={styles.debugError}>Error: {tokenInfo.error}</div>
      ) : tokenInfo ? (
        <div className={styles.debugJson}>
          {/* Usage Summary */}
          <div className={styles.debugMetric}>
            <span className={styles.debugLabel}>Total Tokens:</span>
            <span>{tokenInfo.totalEstimate.toLocaleString()}</span>
          </div>
          <div className={styles.debugMetric}>
            <span className={styles.debugLabel}>Total Cost:</span>
            <span className={styles.totalCost}>
              ${tokenInfo.costs?.total.toFixed(6) || "0.000000"}
            </span>
          </div>

          {/* Breakdown by Category */}
          <div className={styles.debugMetric}>
            <span className={styles.debugLabel}>1. NLP (Text Processing):</span>
            <span>
              {tokenInfo.userInput.estimatedTokens} tokens •{" "}
              {tokenInfo.costs?.modelName || "Unknown"} • $
              {tokenInfo.costs?.nlp.toFixed(6) || "0.000000"}
            </span>
          </div>

          {tokenInfo.imageProcessing.commandCount > 0 && (
            <div className={styles.debugMetric}>
              <span className={styles.debugLabel}>
                2. Image (Visual Processing):
              </span>
              <div>
                <div>
                  {tokenInfo.imageProcessing.estimatedTokens.toLocaleString()}{" "}
                  tokens • Nano Banana • $
                  {tokenInfo.costs?.image.toFixed(6) || "0.000000"}
                </div>
              </div>
            </div>
          )}

          {tokenInfo.videoProcessing.commandCount > 0 && (
            <div className={styles.debugMetric}>
              <span className={styles.debugLabel}>
                3. Video (Veo-3 Generation):
              </span>
              <div>
                <div>
                  Google Veo-3 • $
                  {tokenInfo.costs?.video.toFixed(6) || "0.000000"}
                </div>
                {tokenInfo.videoProcessing.metadata && (
                  <div>
                    <small>
                      {tokenInfo.videoProcessing.metadata.generation
                        ?.resolution || "720p"}{" "}
                      •
                      {tokenInfo.videoProcessing.metadata.duration?.display ||
                        "8s"}{" "}
                      •
                      {tokenInfo.videoProcessing.metadata.generation
                        ?.aspect_ratio || "16:9"}
                    </small>
                  </div>
                )}
              </div>
            </div>
          )}

          {tokenInfo.nanoBanana && (
            <div className={styles.debugMetric}>
              <span className={styles.debugLabel}>Nano Banana:</span>
              <span
                className={
                  tokenInfo.nanoBanana.available
                    ? styles.statusGreen
                    : styles.statusRed
                }
              >
                {tokenInfo.nanoBanana.available ? "Available" : "Not Available"}
                {tokenInfo.nanoBanana.error &&
                  ` (${tokenInfo.nanoBanana.error})`}
              </span>
            </div>
          )}

          {tokenInfo.totalEstimate > 800 && (
            <div className={styles.debugTip}>
              High token usage - may quickly consume daily quota on free tier
            </div>
          )}

          {tokenInfo.costs && tokenInfo.costs.total > 0.001 && (
            <div className={styles.debugTip}>
              Cost per interaction: ${tokenInfo.costs.total.toFixed(6)} (~$
              {(tokenInfo.costs.total * 1000).toFixed(3)} per 1000 interactions)
            </div>
          )}
        </div>
      ) : (
        <div className={styles.debugLoading}>Analyzing tokens...</div>
      )}
    </div>
  );
}

export default function AssistantMessage({
  message,
  sessionName,
  keyPrefix,
  sessionId,
  allMessages,
  currentIndex,
}: AssistantMessageProps) {
  // Set default expansion based on message role
  const getDefaultExpanded = useCallback(() => {
    return true; // Assistant messages open by default
  }, []);

  const [isExpanded, setIsExpanded] = useState(getDefaultExpanded());
  const [activeTab, setActiveTab] = useState<"response" | "debug">("response");

  // Find the actual user input from the previous message
  const getUserInput = () => {
    if (allMessages && currentIndex !== undefined && currentIndex > 0) {
      const previousMessage = allMessages[currentIndex - 1];
      if (previousMessage && previousMessage.role === 'user') {
        return previousMessage.content;
      }
    }
    return message.content || "No user input captured";
  };

  // Reset expanded state when sessionId changes
  useEffect(() => {
    setIsExpanded(getDefaultExpanded());
  }, [sessionId, getDefaultExpanded]);

  return (
    <div key={keyPrefix} className={`${styles.message} ${styles.assistant}`}>
      <div
        className={`${styles.messageHeader} ${styles.clickable}`}
        onClick={() => setIsExpanded(!isExpanded)}
        title={isExpanded ? "Click to collapse" : "Click to expand"}
        style={{
          cursor: "pointer",
        }}
      >
        <div className={styles.headerLeft}></div>
        <div className={styles.headerRight}>
          {sessionName && (
            <span className={styles.sessionName}>{sessionName}</span>
          )}
        </div>
      </div>

      {isExpanded && (
        <>
          {/* Tab Navigation */}
          <div className={styles.tabContainer}>
            <div className={styles.tabButtons}>
              <button
                className={`${styles.tabButton} ${
                  activeTab === "response" ? styles.activeTab : ""
                }`}
                onClick={() => setActiveTab("response")}
              >
                Response
              </button>
              <button
                className={`${styles.tabButton} ${
                  activeTab === "debug" ? styles.activeTab : ""
                }`}
                onClick={() => setActiveTab("debug")}
              >
                Debug
              </button>
            </div>
          </div>

          {/* Tab Content */}
          <div className={styles.tabContent}>
            {activeTab === "response" && (
              <div className={styles.responseTab}>
                {message.explanation && (
                  <div className={styles.aiSection}>
                    <p>{message.explanation}</p>
                  </div>
                )}

                {message.fallback && (
                  <div className={styles.aiSection}>
                    <strong>FALLBACK RESPONSE</strong>
                    <p>
                      This response was generated as a fallback when the primary
                      AI processing failed.
                    </p>
                  </div>
                )}

                <ExecutionResults
                  executionResults={message.execution_results}
                  excludeImages={false}
                />
              </div>
            )}

            {activeTab === "debug" && (
              <div className={styles.debugTab}>
                <div className={styles.debugHeader}>
                  <strong>DEBUG LOG</strong>
                  <button
                    onClick={() => {
                      const debugData = {
                        timestamp: message.timestamp || new Date().toISOString(),
                        user_input: getUserInput(),
                        ai_explanation: message.explanation || "",
                        generated_commands: message.commands || [],
                        expected_result: message.expectedResult || "",
                        processing_error: message.error || null,
                        fallback_used: message.fallback || false,
                        execution_results: (message.execution_results || []).map((result) => ({
                          command: result.command,
                          success: result.success,
                          error: result.error || null,
                          result: result.result || null,
                        })),
                        session_id: sessionId || "no_session",
                        model_used: message.model_used || "unknown",
                      };
                      navigator.clipboard.writeText(
                        JSON.stringify(debugData, null, 2)
                      );
                    }}
                    className={styles.copyButton}
                  >
                    Copy Debug Log
                  </button>
                </div>

                <pre className={styles.debugContent}>
                  {JSON.stringify(
                    {
                      timestamp: message.timestamp || new Date().toISOString(),
                      user_input: getUserInput(),
                      ai_explanation: message.explanation || "",
                      generated_commands: message.commands || [],
                      expected_result: message.expectedResult || "",
                      processing_error: message.error || null,
                      fallback_used: message.fallback || false,
                      execution_results: (message.execution_results || []).map((result) => ({
                        command: result.command,
                        success: result.success,
                        error: result.error || null,
                        result: result.result || null,
                      })),
                      session_id: sessionId || "no_session",
                      model_used: message.model_used || "unknown",
                    },
                    null,
                    2
                  )}
                </pre>
				<br />
				<TokenAnalysisPanel message={message} />
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
