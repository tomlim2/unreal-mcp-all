'use client';

import { useState, useEffect, useCallback } from 'react';
import styles from './MessageItem.module.css';
import CommandsDisplay from './CommandsDisplay';
import ExecutionResults from './ExecutionResults';
import MessageItemImageResult from './MessageItemImageResult';

interface ExecutionResultData {
  command: string;
  success: boolean;
  result?: unknown;
  error?: string;
}

interface ChatMessage {
  timestamp: string;
  role: 'user' | 'assistant' | 'system';
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
}

// Token Analysis Panel Component
function TokenAnalysisPanel({ message }: { message: ChatMessage }) {
  const [tokenInfo, setTokenInfo] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const calculateCosts = (tokens: number, imageTokens: number, modelUsed?: string, backendImageCost?: number) => {
    // Model-specific pricing (as of 2024)
    const MODEL_PRICING = {
      'gemini': {
        input: 0.000075 / 1000,   // $0.075 per 1M tokens (Gemini-1.5-Flash)
        output: 0.0003 / 1000,    // $0.30 per 1M tokens
        name: 'Gemini-1.5-Flash'
      },
      'gemini-2': {
        input: 0.000075 / 1000,   // $0.075 per 1M tokens (Gemini-2.5-Flash)  
        output: 0.0003 / 1000,    // $0.30 per 1M tokens
        name: 'Gemini-2.5-Flash'
      },
      'claude': {
        input: 0.003 / 1000,      // $3.00 per 1M tokens (Claude-3-Sonnet)
        output: 0.015 / 1000,     // $15.00 per 1M tokens
        name: 'Claude-3-Sonnet'
      },
      'claude-3-haiku-20240307': {
        input: 0.00025 / 1000,    // $0.25 per 1M tokens (Claude-3-Haiku)
        output: 0.00125 / 1000,   // $1.25 per 1M tokens
        name: 'Claude-3-Haiku'
      }
    };

    // Image processing pricing (Gemini image generation - 2025 pricing)
    const GEMINI_IMAGE_GENERATION = 0.03 / 1000;  // $30.00 per 1M tokens (image generation)

    // Get model pricing, default to gemini-2 if unknown
    const modelKey = modelUsed || 'gemini-2';
    const pricing = MODEL_PRICING[modelKey] || MODEL_PRICING['gemini-2'];

    // Estimate input/output split (rough approximation)
    const inputTokens = Math.ceil(tokens * 0.7); // 70% input
    const outputTokens = Math.floor(tokens * 0.3); // 30% output

    const nlpCost = (inputTokens * pricing.input) + (outputTokens * pricing.output);
    // Use backend-provided cost if available, otherwise fall back to frontend calculation
    const imageCost = backendImageCost !== undefined && backendImageCost > 0 
      ? backendImageCost 
      : (imageTokens > 0 ? (imageTokens * GEMINI_IMAGE_GENERATION) : 0);
    
    return {
      nlp: nlpCost,
      image: imageCost,
      total: nlpCost + imageCost,
      modelName: pricing.name
    };
  };

  const analyzeTokens = async () => {
    setLoading(true);
    try {
      // Estimate tokens from user input
      const userInput = message.content || '';
      const hasNonAscii = /[^\x00-\x7F]/.test(userInput);
      const charCount = userInput.length;
      const estimatedTokens = hasNonAscii ? Math.ceil(charCount / 2.5) : Math.ceil(charCount / 4);
      
      // Check if this involved image commands (Nano Banana)
      const imageCommands = (message.commands || []).filter(cmd => 
        cmd.type === 'transform_image_style' || cmd.type === 'take_styled_screenshot'
      );
      
      let imageTokenEstimate = 0;
      let imageMetadata = null;
      
      if (imageCommands.length > 0) {
        // Look for actual image metadata in execution results
        const imageResults = (message.execution_results || []).find(result => 
          result.result && typeof result.result === 'object' && 
          (result.result as any).image_metadata
        );
        
        if (imageResults && (imageResults.result as any).image_metadata) {
          imageMetadata = (imageResults.result as any).image_metadata;
          // Use actual token count from backend calculation
          imageTokenEstimate = imageMetadata.tokens || 900;
        } else {
          // Fallback to conservative estimate
          imageTokenEstimate = imageCommands.length * 900;
        }
      }

      // Calculate costs with model-specific pricing
      // If backend provides cost calculation, use that for images; otherwise calculate
      let backendImageCost = 0;
      if (imageMetadata && imageMetadata.estimated_cost) {
        // Parse cost from backend (format: "$0.003")
        const costMatch = imageMetadata.estimated_cost.match(/\$(\d+\.?\d*)/);
        if (costMatch) {
          backendImageCost = parseFloat(costMatch[1]);
        }
      }
      
      const costs = calculateCosts(estimatedTokens, imageTokenEstimate, message.model_used, backendImageCost);

      // Check Nano Banana status
      let nanoBananaStatus = null;
      try {
        const response = await fetch('http://localhost:8080/', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({action: 'check_nano_banana'})
        });
        nanoBananaStatus = await response.json();
      } catch (e) {
        console.log('Could not fetch Nano Banana status:', e);
      }

      setTokenInfo({
        userInput: {
          characters: charCount,
          estimatedTokens,
          hasNonAscii,
          language: hasNonAscii ? 'Non-English' : 'English'
        },
        imageProcessing: {
          commandCount: imageCommands.length,
          estimatedTokens: imageTokenEstimate,
          commands: imageCommands.map(cmd => cmd.type),
          metadata: imageMetadata
        },
        totalEstimate: estimatedTokens + imageTokenEstimate,
        costs: costs,
        nanoBanana: nanoBananaStatus?.nano_banana || null
      });
    } catch (error) {
      console.error('Token analysis failed:', error);
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
          <button onClick={analyzeTokens} disabled={loading} className={styles.copyButton}>
            {loading ? '⟳' : '↻'} Refresh
          </button>
          <button 
            onClick={() => {
              if (!tokenInfo || tokenInfo.error) return;
              
              let analysisText = "# Token Analysis\n\n";
              
              // Usage Summary
              analysisText += `## Usage Summary\n`;
              analysisText += `- Total Tokens: ${tokenInfo.totalEstimate.toLocaleString()}\n`;
              analysisText += `- Total Cost: $${tokenInfo.costs.total.toFixed(6)}\n\n`;
              
              // Breakdown by Category
              analysisText += `## Breakdown by Category\n`;
              analysisText += `1. **NLP (Text Processing)**\n`;
              analysisText += `   - Tokens: ${tokenInfo.userInput.estimatedTokens}\n`;
              analysisText += `   - Model: ${tokenInfo.costs.modelName}\n`;
              analysisText += `   - Cost: $${tokenInfo.costs.nlp.toFixed(6)}\n\n`;
              
              if (tokenInfo.imageProcessing.commandCount > 0) {
                analysisText += `2. **Image (Visual Processing)**\n`;
                analysisText += `   - Tokens: ${tokenInfo.imageProcessing.estimatedTokens.toLocaleString()}\n`;
                analysisText += `   - Service: Nano Banana\n`;
                if (tokenInfo.imageProcessing.metadata) {
                  const meta = tokenInfo.imageProcessing.metadata;
                  analysisText += `   - Image Details: ${meta.processed_size || meta.original_size} • ${meta.file_size}\n`;
                }
                analysisText += `   - Cost: $${tokenInfo.costs.image.toFixed(6)}\n\n`;
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
            <span className={styles.totalCost}>${tokenInfo.costs?.total.toFixed(6) || '0.000000'}</span>
          </div>
          
          {/* Breakdown by Category */}
          <div className={styles.debugMetric}>
            <span className={styles.debugLabel}>1. NLP (Text Processing):</span>
            <span>{tokenInfo.userInput.estimatedTokens} tokens • {tokenInfo.costs?.modelName || 'Unknown'} • ${tokenInfo.costs?.nlp.toFixed(6) || '0.000000'}</span>
          </div>
          
          {tokenInfo.imageProcessing.commandCount > 0 && (
            <div className={styles.debugMetric}>
              <span className={styles.debugLabel}>2. Image (Visual Processing):</span>
              <div>
                <div>{tokenInfo.imageProcessing.estimatedTokens.toLocaleString()} tokens • Nano Banana • ${tokenInfo.costs?.image.toFixed(6) || '0.000000'}</div>
                {tokenInfo.imageProcessing.metadata && (
                  <div style={{fontSize: '0.9em', color: '#666', marginTop: '2px'}}>
                    {tokenInfo.imageProcessing.metadata.processed_size || tokenInfo.imageProcessing.metadata.original_size} • {tokenInfo.imageProcessing.metadata.file_size}
                  </div>
                )}
              </div>
            </div>
          )}

          {tokenInfo.nanoBanana && (
            <div className={styles.debugMetric}>
              <span className={styles.debugLabel}>Nano Banana:</span>
              <span className={tokenInfo.nanoBanana.available ? styles.statusGreen : styles.statusRed}>
                {tokenInfo.nanoBanana.available ? 'Available' : 'Not Available'}
                {tokenInfo.nanoBanana.error && ` (${tokenInfo.nanoBanana.error})`}
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
              Cost per interaction: ${tokenInfo.costs.total.toFixed(6)} (~${(tokenInfo.costs.total * 1000).toFixed(3)} per 1000 interactions)
            </div>
          )}
        </div>
      ) : (
        <div className={styles.debugLoading}>Analyzing tokens...</div>
      )}
    </div>
  );
}


export default function AssistantMessage({ message, sessionName, keyPrefix, sessionId }: AssistantMessageProps) {
  // Set default expansion based on message role
  const getDefaultExpanded = useCallback(() => {
    return true; // Assistant messages open by default
  }, []);
  
  const [isExpanded, setIsExpanded] = useState(getDefaultExpanded());
  const [activeTab, setActiveTab] = useState<'response' | 'debug'>('response');

  // Reset expanded state when sessionId changes
  useEffect(() => {
    setIsExpanded(getDefaultExpanded());
  }, [sessionId, getDefaultExpanded]);


  return (
    <div 
      key={keyPrefix} 
      className={`${styles.message} ${styles.assistant}`}
    >
      <div 
        className={`${styles.messageHeader} ${styles.clickable}`}
        onClick={() => setIsExpanded(!isExpanded)}
        title={isExpanded ? "Click to collapse" : "Click to expand"}
        style={{
          cursor: 'pointer'
        }}
      >
        <div className={styles.headerLeft}>
        </div>
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
                className={`${styles.tabButton} ${activeTab === 'response' ? styles.activeTab : ''}`}
                onClick={() => setActiveTab('response')}
              >
                Response
              </button>
              <button
                className={`${styles.tabButton} ${activeTab === 'debug' ? styles.activeTab : ''}`}
                onClick={() => setActiveTab('debug')}
              >
                Debug
              </button>
            </div>
          </div>

          {/* Tab Content */}
          <div className={styles.tabContent}>
            {activeTab === 'response' && (
              <div className={styles.responseTab}>
                <div className={styles.messageContent}>
                  {message.content}
                </div>
                
                {message.explanation && (
                  <div className={styles.aiSection}>
                    <strong>EXPLANATION:</strong>
                    <p>{message.explanation}</p>
                  </div>
                )}
                
                {message.expectedResult && (
                  <div className={styles.aiSection}>
                    <strong>EXPECTED RESULT:</strong>
                    <p>{message.expectedResult}</p>
                  </div>
                )}
                
                {message.error && (
                  <div className={styles.aiSection}>
                    <strong>ERROR:</strong>
                    <p>{message.error}</p>
                  </div>
                )}
                
                {message.fallback && (
                  <div className={styles.aiSection}>
                    <strong>FALLBACK RESPONSE</strong>
                    <p>This response was generated as a fallback when the primary AI processing failed.</p>
                  </div>
                )}
                
                <ExecutionResults 
                  executionResults={message.execution_results}
                  excludeImages={false}
                />
              </div>
            )}

            {activeTab === 'debug' && (
              <div className={styles.debugTab}>
                {/* Execution time at the top */}
                <div className={styles.debugExecutionTime}>
                  {new Date(message.timestamp).toLocaleString()}
                </div>
                
                <TokenAnalysisPanel message={message} />
                
                <div className={styles.debugHeader}>
                  <strong>DEBUG FORMAT</strong>
                  <button 
                    onClick={() => {
                      const debugData = {
                        conversation_context: {
                          user_input: message.content || "No user input captured",
                          timestamp: message.timestamp || new Date().toISOString()
                        },
                        ai_processing: {
                          explanation: message.explanation || "",
                          generated_commands: message.commands || [],
                          expected_result: message.expectedResult || "",
                          processing_error: message.error || null,
                          fallback_used: message.fallback || false
                        },
                        execution_results: (message.execution_results || []).map(result => ({
                          command_type: result.command,
                          success: result.success,
                          result_data: result.result || null,
                          error_message: result.error || null
                        })),
                        debug_notes: {
                          message_role: message.role,
                          session_context: sessionId ? `Session: ${sessionId}` : "No session context"
                        }
                      };
                      navigator.clipboard.writeText(JSON.stringify(debugData, null, 2));
                    }}
                    className={styles.copyButton}
                  >
                    Copy JSON
                  </button>
                </div>
                
                <pre className={styles.debugContent}>
                  <div className={styles.debugBlock}>
                    <div className={styles.debugLabel}>CONVERSATION CONTEXT:</div>
                    <div className={styles.debugJson}>
{JSON.stringify({
  user_input: message.content || "No user input captured",
  timestamp: message.timestamp || new Date().toISOString()
}, null, 2)}
                    </div>
                  </div>
                  <div className={styles.debugBlock}>
                    <div className={styles.debugLabel}>AI PROCESSING:</div>
                    <div className={styles.debugJson}>
{JSON.stringify({
  explanation: message.explanation || "",
  generated_commands: message.commands || [],
  expected_result: message.expectedResult || "",
  processing_error: message.error || null,
  fallback_used: message.fallback || false
}, null, 2)}
                    </div>
                  </div>
                  
                  {message.execution_results && message.execution_results.length > 0 && (
                    <div className={styles.debugBlock}>
                      <div className={styles.debugLabel}>EXECUTION RESULTS:</div>
                      <div className={styles.debugJson}>
{JSON.stringify(message.execution_results.map(result => ({
  command_type: result.command,
  success: result.success,
  result_data: result.result || null,
  error_message: result.error || null
})), null, 2)}
                      </div>
                    </div>
                  )}
                  
                  <div className={styles.debugBlock}>
                    <div className={styles.debugLabel}>DEBUG NOTES:</div>
                    <div className={styles.debugJson}>
{JSON.stringify({
  message_role: message.role,
  session_context: sessionId ? `Session: ${sessionId}` : "No session context"
}, null, 2)}
                    </div>
                  </div>
                </pre>
              </div>
            )}
          </div>
        </>
      )}

    </div>
  );
}