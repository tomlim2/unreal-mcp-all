'use client';

import { useState, useEffect, useCallback } from 'react';
import styles from './MessageItem.module.css';
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

interface MessageItemProps {
  message: ChatMessage;
  sessionName?: string;
  index: number;
  sessionId?: string;
}

export default function MessageItem({ message, sessionName, index, sessionId }: MessageItemProps) {
  const keyPrefix = sessionId ? `${sessionId}-${index}` : index;
  
  // Set default expansion based on message role
  const getDefaultExpanded = useCallback(() => {
    if (message.role === 'assistant') return true; // Assistant messages open by default
    return true; // Other messages open
  }, [message.role]);
  
  const [isExpanded, setIsExpanded] = useState(getDefaultExpanded());

  // Reset expanded state when sessionId changes
  useEffect(() => {
    setIsExpanded(getDefaultExpanded());
  }, [sessionId, getDefaultExpanded]);

  // User message rendering
  if (message.role === 'user') {
    return (
      <div key={keyPrefix} className={`${styles.message} ${styles.user}`}>
        <div className={styles.messageHeader}>
          {sessionName && (
            <span className={styles.sessionName}>{sessionName}</span>
          )}
        </div>
        <div className={`${styles.messageContent} ${styles.resultContent}`}>
          {message.content}
        </div>
      </div>
    );
  }

  // Assistant message rendering
  if (message.role === 'assistant') {
    // Determine success/failure status for assistant messages
    const getAssistantStatus = () => {
      if (!message.execution_results || message.execution_results.length === 0) {
        return { status: 'neutral' };
      }
      
      const hasFailures = message.execution_results.some(result => !result.success);
      return hasFailures 
        ? { status: 'failure' }
        : { status: 'success' };
    };

    // Extract image results to show always (not collapsed)
    const imageResults = message.execution_results?.filter(result => 
      result.success && 
      result.result && 
      typeof result.result === 'object' && 
      result.result !== null &&
      'image_url' in result.result
    ) || [];

    const { status } = getAssistantStatus();

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
            <div className={styles.messageContent}>
              {message.content}
            </div>
            
            {message.explanation && (
              <div className={styles.aiSection}>
                <strong>AI EXPLANATION:</strong>
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
                <strong>AI ERROR:</strong>
                <p>{message.error}</p>
              </div>
            )}
            
            {message.fallback && (
              <div className={styles.aiSection}>
                <strong>FALLBACK RESPONSE</strong>
                <p>This response was generated as a fallback when the primary AI processing failed.</p>
              </div>
            )}
            
            {message.commands && message.commands.length > 0 && (
              <div className={styles.commands}>
                <strong>AI Generated Commands:</strong>
                {message.commands.map((cmd, cmdIndex) => (
                  <pre key={cmdIndex} className={styles.command}>
                    <div className={styles.commandHeader}>
                      <strong>{cmd.type}</strong>
                      <span className={styles.languageLabel}>json</span>
                    </div>
                    <div className={styles.commandContent}>
                      {JSON.stringify(cmd.params, null, 2)}
                    </div>
                  </pre>
                ))}
              </div>
            )}
            
            {/* Show non-image execution results only */}
            {(() => {
              const nonImageResults = message.execution_results?.filter(result => !(
                result.result && 
                typeof result.result === 'object' && 
                result.result !== null &&
                'image_url' in result.result
              )) || [];
              
              return nonImageResults.length > 0 && (
                <div className={styles.results}>
                  <strong>Unreal Engine Execution Results:</strong>
                  {nonImageResults.map((result, resultIndex) => (
                    <div key={resultIndex} className={`${styles.result} ${result.success ? styles.success : styles.failure}`}>
                      <div className={styles.resultHeader}>
                        {result.command} - {result.success ? '✅ Success' : '❌ Failed'}
                      </div>
                      <MessageItemImageResult result={result} resultIndex={resultIndex} />
                    </div>
                  ))}
                </div>
              );
            })()}
          </>
        )}
		{/* Always show images (not collapsed) */}
        {imageResults.length > 0 && (
          <div className={styles.alwaysVisibleImages}>
            <strong>Generated Images:</strong>
            {imageResults.map((result, resultIndex) => (
              <div key={`image-${resultIndex}`} className={styles.imageContainer}>
                <MessageItemImageResult result={result} resultIndex={resultIndex} />
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  // System message rendering
  if (message.role === 'system') {
    return (
      <div key={keyPrefix} className={`${styles.message} ${styles.system}`}>
        <div className={styles.messageHeader}>
          <span className={styles.roleLabel}>System</span>
          {sessionName && (
            <span className={styles.sessionName}>{sessionName}</span>
          )}
        </div>
        <div className={styles.messageContent}>
          {message.content}
        </div>
      </div>
    );
  }

  return null;
}