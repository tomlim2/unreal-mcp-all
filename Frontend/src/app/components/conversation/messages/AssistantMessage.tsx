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

  const calculateCosts = (tokens: number, imageTokens: number, modelUsed?: string) => {
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
    const imageCost = imageTokens > 0 ? (imageTokens * GEMINI_IMAGE_GENERATION) : 0;
    
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
          // Use actual token count from metadata
          imageTokenEstimate = imageMetadata.tokens || 900;
        } else {
          // Fallback to conservative estimate
          imageTokenEstimate = imageCommands.length * 900;
        }
      }

      // Calculate costs with model-specific pricing
      const costs = calculateCosts(estimatedTokens, imageTokenEstimate, message.model_used);

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
              
              let analysisText = "# Token Analysis Report\n\n";
              
              // Input text analysis
              analysisText += `## Input Text\n`;
              analysisText += `- Characters: ${tokenInfo.userInput.characters}\n`;
              analysisText += `- Estimated Tokens: ${tokenInfo.userInput.estimatedTokens}\n`;
              analysisText += `- Language: ${tokenInfo.userInput.language}\n\n`;
              
              // Image processing if present
              if (tokenInfo.imageProcessing.commandCount > 0) {
                analysisText += `## Image Processing\n`;
                analysisText += `- Commands: ${tokenInfo.imageProcessing.commandCount} (${tokenInfo.imageProcessing.commands.join(', ')})\n`;
                analysisText += `- Estimated Tokens: ${tokenInfo.imageProcessing.estimatedTokens}\n\n`;
                
                // Image metadata if available
                if (tokenInfo.imageProcessing.metadata) {
                  const meta = tokenInfo.imageProcessing.metadata;
                  analysisText += `## Image Metadata\n`;
                  analysisText += `- Original Size: ${meta.original_size}\n`;
                  analysisText += `- Processed Size: ${meta.processed_size}\n`;
                  analysisText += `- File Size: ${meta.file_size}\n`;
                  analysisText += `- Tokens: ${meta.tokens} (Base: 1290)\n`;
                  analysisText += `- Processing Cost: ${meta.estimated_cost}\n\n`;
                }
              }
              
              // Cost breakdown
              analysisText += `## Cost Analysis\n`;
              analysisText += `- Model Used: ${tokenInfo.costs.modelName}\n`;
              analysisText += `- NLP Processing: $${tokenInfo.costs.nlp.toFixed(6)}\n`;
              if (tokenInfo.costs.image > 0) {
                analysisText += `- Image Processing: $${tokenInfo.costs.image.toFixed(6)}\n`;
              }
              analysisText += `- Total Cost: $${tokenInfo.costs.total.toFixed(6)}\n`;
              analysisText += `- Total Tokens: ${tokenInfo.totalEstimate}\n\n`;
              
              // Nano Banana status
              if (tokenInfo.nanoBanana) {
                analysisText += `## Nano Banana Status\n`;
                analysisText += `- Available: ${tokenInfo.nanoBanana.available ? 'Yes' : 'No'}\n`;
                if (tokenInfo.nanoBanana.error) {
                  analysisText += `- Error: ${tokenInfo.nanoBanana.error}\n`;
                }
                analysisText += `\n`;
              }
              
              // Usage efficiency
              if (tokenInfo.totalEstimate > 800) {
                analysisText += `## Usage Notes\n`;
                analysisText += `- High token usage detected (${tokenInfo.totalEstimate} tokens)\n`;
                analysisText += `- May quickly consume daily quota on free tier\n`;
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
          <div className={styles.debugMetric}>
            <span className={styles.debugLabel}>Input Text:</span>
            <span>{tokenInfo.userInput.characters} chars, ~{tokenInfo.userInput.estimatedTokens} tokens ({tokenInfo.userInput.language})</span>
          </div>
          
          {tokenInfo.imageProcessing.commandCount > 0 && (
            <div className={styles.debugMetric}>
              <span className={styles.debugLabel}>Image Processing:</span>
              <span>{tokenInfo.imageProcessing.commandCount} commands, ~{tokenInfo.imageProcessing.estimatedTokens} tokens</span>
            </div>
          )}
          
          {tokenInfo.imageProcessing.metadata && (
            <div className={styles.debugMetric}>
              <span className={styles.debugLabel}>Image Metadata</span>
              <div className={styles.imageMetadataTable}>
                <div className={styles.metadataRow}>
                  <span className={styles.metadataLabel}>Original:</span>
                  <span className={styles.metadataValue}>{tokenInfo.imageProcessing.metadata.original_size}</span>
                </div>
                <div className={styles.metadataRow}>
                  <span className={styles.metadataLabel}>Processed:</span>
                  <span className={styles.metadataValue}>{tokenInfo.imageProcessing.metadata.processed_size}</span>
                </div>
                <div className={styles.metadataRow}>
                  <span className={styles.metadataLabel}>File Size:</span>
                  <span className={styles.metadataValue}>{tokenInfo.imageProcessing.metadata.file_size}</span>
                </div>
                <div className={styles.metadataRow}>
                  <span className={styles.metadataLabel}>Tokens:</span>
                  <span className={styles.metadataValue}>{tokenInfo.imageProcessing.metadata.tokens} (Base: 1290)</span>
                </div>
                <div className={styles.metadataRow}>
                  <span className={styles.metadataLabel}>Cost:</span>
                  <span className={styles.metadataValue}>{tokenInfo.imageProcessing.metadata.estimated_cost}</span>
                </div>
              </div>
            </div>
          )}
          
          <div className={styles.debugMetric}>
            <span className={styles.debugLabel}>Total Estimate:</span>
            <span className={tokenInfo.totalEstimate > 500 ? styles.highUsage : styles.normalUsage}>
              ~{tokenInfo.totalEstimate} tokens
            </span>
          </div>

          {tokenInfo.costs && (
            <>
              <div className={styles.debugMetric}>
                <span className={styles.debugLabel}>Cost Breakdown:</span>
                <div className={styles.costBreakdown}>
                  <div>{tokenInfo.costs.modelName} (NLP): ${tokenInfo.costs.nlp.toFixed(6)}</div>
                  {tokenInfo.costs.image > 0 && (
                    <div>Gemini (Images): ${tokenInfo.costs.image.toFixed(6)}</div>
                  )}
                  <div className={styles.totalCost}>Total: ${tokenInfo.costs.total.toFixed(6)}</div>
                </div>
              </div>
            </>
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