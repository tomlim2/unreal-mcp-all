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
      if (imageCommands.length > 0) {
        // Image generation prompts typically use 800-1000+ tokens
        imageTokenEstimate = imageCommands.length * 900; // Conservative estimate
      }

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
          commands: imageCommands.map(cmd => cmd.type)
        },
        totalEstimate: estimatedTokens + imageTokenEstimate,
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
    <div className={styles.debugAnalysisPanel}>
      <div className={styles.debugPanelHeader}>
        <strong>Token Analysis</strong>
        <button onClick={analyzeTokens} disabled={loading} className={styles.refreshButton}>
          {loading ? '⟳' : '↻'} Refresh
        </button>
      </div>
      
      {tokenInfo?.error ? (
        <div className={styles.debugError}>Error: {tokenInfo.error}</div>
      ) : tokenInfo ? (
        <div className={styles.debugPanelContent}>
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
          
          <div className={styles.debugMetric}>
            <span className={styles.debugLabel}>Total Estimate:</span>
            <span className={tokenInfo.totalEstimate > 500 ? styles.highUsage : styles.normalUsage}>
              ~{tokenInfo.totalEstimate} tokens
            </span>
          </div>

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