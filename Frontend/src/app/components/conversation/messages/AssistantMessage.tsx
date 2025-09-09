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