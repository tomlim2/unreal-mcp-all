"use client";

import { useState, useEffect, useCallback } from "react";
import styles from "./MessageItem.module.css";
import ExecutionResults from "./ExecutionResults";

interface ExecutionResultData {
  command: string;
  success: boolean;
  result?: unknown;
  error?: string;
  // Optional diagnostics from backend (match ExecutionResults.tsx)
  error_code?: string;
  error_details?: Record<string, unknown>;
  suggestion?: string;
  category?: string;
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
  // Types for hierarchical execution result payloads
  interface ImageMetadata {
    size?: { processed?: string; original?: string };
    file_size?: { display?: string };
    // Allow additional vendor-specific fields
    [key: string]: unknown;
  }

  interface VideoMetadata {
    duration?: { display?: string };
    generation?: { resolution?: string; aspect_ratio?: string; prompt?: string };
    [key: string]: unknown;
  }

  interface HierarchicalResult {
    image?: { metadata?: ImageMetadata };
    video?: { metadata?: VideoMetadata };
    cost?: { tokens?: number; value?: number };
  }

  type FullTokenInfo = {
    userInput: {
      characters: number;
      estimatedTokens: number;
      hasNonAscii: boolean;
      language: string;
    };
    imageProcessing: {
      commandCount: number;
      estimatedTokens: number;
      commands: string[];
      metadata: ImageMetadata | null;
    };
    videoProcessing: {
      commandCount: number;
      commands: string[];
      metadata: VideoMetadata | null;
      cost: number;
    };
    totalEstimate: number;
    costs: {
      nlp: number;
      image: number;
      video: number;
      total: number;
      modelName: string;
    };
  };

  type TokenInfo = FullTokenInfo | { error: string };

  const [tokenInfo, setTokenInfo] = useState<TokenInfo | null>(null);
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
    } as const;

    type ModelKey = keyof typeof MODEL_PRICING;
    const isModelKey = (key: string): key is ModelKey => key in MODEL_PRICING;

    // Image processing pricing (Gemini image generation - 2025 pricing)
    const GEMINI_IMAGE_GENERATION = 0.03 / 1000; // $30.00 per 1M tokens (image generation)

    // Get model pricing, default to gemini-2 if unknown
  const modelKeyStr = modelUsed ?? "gemini-2";
  const pricing = MODEL_PRICING[isModelKey(modelKeyStr) ? modelKeyStr : "gemini-2"];

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
  let imageMetadata: ImageMetadata | null = null;

      if (imageCommands.length > 0) {
        // Look for actual image metadata in execution results
        const imageResults = (message.execution_results || []).find((res) => {
          const rr = res?.result as unknown;
          if (rr && typeof rr === "object") {
            const hr = rr as Partial<HierarchicalResult>;
            return Boolean(hr.image?.metadata || hr.cost?.tokens);
          }
          return false;
        });

        if (imageResults && imageResults.result && typeof imageResults.result === "object") {
          const resultData = imageResults.result as Partial<HierarchicalResult>;

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
  let videoMetadata: VideoMetadata | null = null;
      let backendVideoCost = 0;

      if (videoCommands.length > 0) {
        // Look for actual video metadata in execution results
        const videoResults = (message.execution_results || []).find((res) => {
          const rr = res?.result as unknown;
          if (rr && typeof rr === "object") {
            const hr = rr as Partial<HierarchicalResult>;
            return Boolean(hr.video?.metadata || hr.cost?.value);
          }
          return false;
        });

        if (videoResults && videoResults.result && typeof videoResults.result === "object") {
          const resultData = videoResults.result as Partial<HierarchicalResult>;

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
        const resultData = imageResults.result as Partial<HierarchicalResult>;

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
      setTokenInfo({ error: error instanceof Error ? error.message : String(error) });
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
      <div className={styles.debugCodeBlock}>
        <div className={styles.debugHeader}>
          <span className={styles.codeBlockTitle}>Token Analysis</span>
          <button
            onClick={() => {
              if (!tokenInfo || ("error" in tokenInfo)) return;

              let analysisText = "# Token Analysis\n\n";

              // Usage Summary
              analysisText += `## Usage Summary\n`;
              const info = tokenInfo as FullTokenInfo;
              analysisText += `- Total Tokens: ${info.totalEstimate.toLocaleString()}\n`;
              analysisText += `- Total Cost: $${info.costs.total.toFixed(
                6
              )}\n\n`;

              // Breakdown by Category
              analysisText += `## Breakdown by Category\n`;
              analysisText += `1. **NLP (Text Processing)**\n`;
              analysisText += `   - Tokens: ${info.userInput.estimatedTokens}\n`;
              analysisText += `   - Model: ${info.costs.modelName}\n`;
              analysisText += `   - Cost: $${info.costs.nlp.toFixed(
                6
              )}\n\n`;

              if (info.imageProcessing.commandCount > 0) {
                analysisText += `2. **Image (Visual Processing)**\n`;
                analysisText += `   - Tokens: ${info.imageProcessing.estimatedTokens.toLocaleString()}\n`;
                analysisText += `   - Service: Nano Banana\n`;
                if (info.imageProcessing.metadata) {
                  const meta = info.imageProcessing.metadata;
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
                analysisText += `   - Cost: $${info.costs.image.toFixed(
                  6
                )}\n\n`;
              }

              if (info.videoProcessing.commandCount > 0) {
                analysisText += `3. **Video (Veo-3 Generation)**\n`;
                analysisText += `   - Service: Google Veo-3\n`;
                if (info.videoProcessing.metadata) {
                  const meta = info.videoProcessing.metadata;
                  const duration = meta.duration?.display || "8s";
                  const resolution = meta.generation?.resolution || "720p";
                  const aspectRatio = meta.generation?.aspect_ratio || "16:9";

                  analysisText += `   - Video Details: ${resolution} (${aspectRatio}) • ${duration}\n`;
                  if (meta.generation?.prompt) {
                    analysisText += `   - Prompt: ${meta.generation.prompt}\n`;
                  }
                }
                analysisText += `   - Cost: $${info.costs.video.toFixed(
                  6
                )}\n\n`;
              }

              // High usage warning
              if (info.totalEstimate > 800) {
                analysisText += `⚠️ High usage (${info.totalEstimate} tokens) - may consume daily quota quickly\n\n`;
              }

              navigator.clipboard.writeText(analysisText);
            }}
            className={styles.copyButton}
            disabled={!tokenInfo || ("error" in tokenInfo)}
            title="Copy Analysis"
          >
            📋
          </button>
        </div>

        {tokenInfo && ("error" in tokenInfo) ? (
          <div className={styles.debugError}>Error: {tokenInfo.error}</div>
        ) : tokenInfo ? (
          <div className={styles.debugJson}>
            {/* Usage Summary */}
            {(() => {
              const info = tokenInfo as FullTokenInfo;
              return (
                <>
                  <div className={styles.debugMetric}>
                    <span className={styles.debugLabel}>Total Tokens:</span>
                    <span>{info.totalEstimate.toLocaleString()}</span>
                  </div>
                  <div className={styles.debugMetric}>
                    <span className={styles.debugLabel}>Total Cost:</span>
                    <span className={styles.totalCost}>
                      ${info.costs.total.toFixed(6)}
                    </span>
                  </div>
                  <div className={styles.debugMetric}>
                    <span className={styles.debugLabel}>1. NLP (Text Processing):</span>
                    <span>
                      {info.userInput.estimatedTokens} tokens • {info.costs.modelName} • ${info.costs.nlp.toFixed(6)}
                    </span>
                  </div>

                  {info.imageProcessing.commandCount > 0 && (
                    <div className={styles.debugMetric}>
                      <span className={styles.debugLabel}>2. Image (Visual Processing):</span>
                      <div>
                        <div>
                          {info.imageProcessing.estimatedTokens.toLocaleString()} tokens • Nano Banana • ${info.costs.image.toFixed(6)}
                        </div>
                      </div>
                    </div>
                  )}

                  {info.videoProcessing.commandCount > 0 && (
                    <div className={styles.debugMetric}>
                      <span className={styles.debugLabel}>3. Video (Veo-3 Generation):</span>
                      <div>
                        <div>
                          Google Veo-3 • ${info.costs.video.toFixed(6)}
                        </div>
                        {info.videoProcessing.metadata && (
                          <div>
                            <small>
                              {info.videoProcessing.metadata.generation?.resolution || "720p"} ({info.videoProcessing.metadata.generation?.aspect_ratio || "16:9"}) • {info.videoProcessing.metadata.duration?.display || "8s"}
                            </small>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {info.totalEstimate > 800 && (
                    <div className={styles.debugTip}>
                      High token usage - may quickly consume daily quota on free tier
                    </div>
                  )}
                </>
              );
            })()}
          </div>
        ) : (
          <div className={styles.debugLoading}>Analyzing tokens...</div>
        )}
      </div>
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

  const [isExpanded, setIsExpanded] = useState<boolean>(getDefaultExpanded());
  const [activeTab, setActiveTab] = useState<"closed-debug" | "open-debug">("closed-debug");

  // Find the actual user input from the previous message
  const getUserInput = () => {
    if (allMessages && currentIndex !== undefined && currentIndex > 0) {
      const previousMessage = allMessages[currentIndex - 1];
      if (previousMessage && previousMessage.role === "user") {
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
  onClick={() => setIsExpanded((prev) => !prev)}
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
          {/* Tab Content */}
          <div className={styles.tabContent}>
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
          </div>
          {/* Tab Navigation */}
          <div className={styles.tabContainer}>
            <div className={styles.tabButtons}>
              <button
                className={`${styles.tabButton} ${
                  activeTab === "closed-debug" ? styles.activeTab : ""
                }`}
                onClick={() => setActiveTab("closed-debug")}
              >
                Close Debug
              </button>
              <button
                className={`${styles.tabButton} ${
                  activeTab === "open-debug" ? styles.activeTab : ""
                }`}
                onClick={() => setActiveTab("open-debug")}
              >
                Open Debug
              </button>
            </div>
          </div>
          {activeTab === "open-debug" && (
            <div className={styles.debugTab}>
              <div className={styles.debugCodeBlock}>
                <div className={styles.debugHeader}>
                  <span className={styles.codeBlockTitle}>Debug Log</span>
                  <button
                    onClick={() => {
                      const debugData = {
                        timestamp:
                          message.timestamp || new Date().toISOString(),
                        user_input: getUserInput(),
                        ai_explanation: message.explanation || "",
                        generated_commands: message.commands || [],
                        expected_result: message.expectedResult || "",
                        processing_error: message.error || null,
                        fallback_used: message.fallback || false,
                        execution_results: (
                          message.execution_results || []
                        ).map((result) => ({
                          command: result.command,
                          success: result.success,
                          error: result.error || null,
                          error_code: result.error_code,
                          category: result.category,
                          error_details: result.error_details,
                          suggestion: result.suggestion,
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
                    title="Copy Debug Log"
                  >
                    📋
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
                      execution_results: (message.execution_results || []).map(
                        (result) => ({
                          command: result.command,
                          success: result.success,
                          error: result.error || null,
                          error_code: result.error_code,
                          category: result.category,
                          error_details: result.error_details,
                          suggestion: result.suggestion,
                          result: result.result || null,
                        })
                      ),
                      session_id: sessionId || "no_session",
                      model_used: message.model_used || "unknown",
                    },
                    null,
                    2
                  )}
                </pre>
              </div>

              <TokenAnalysisPanel message={message} />
            </div>
          )}
        </>
      )}
    </div>
  );
}
