'use client';

import { useState, useEffect } from 'react';
import styles from './MessageItem.module.css';

interface ChatMessage {
  timestamp: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  commands?: Array<{
    type: string;
    params: Record<string, unknown>;
  }>;
  execution_results?: Array<{
    command: string;
    success: boolean;
    result?: unknown;
    error?: string;
  }>;
}

interface MessageItemProps {
  message: ChatMessage;
  sessionName?: string;
  index: number;
  sessionId?: string;
  previousMessage?: ChatMessage;
}

export default function MessageItem({ message, sessionName, index, sessionId, previousMessage }: MessageItemProps) {
  const keyPrefix = sessionId ? `${sessionId}-${index}` : index;
  const [showDetails, setShowDetails] = useState(false);

  // Reset showDetails when sessionId changes
  useEffect(() => {
    setShowDetails(false);
  }, [sessionId]);

  const isAssistant = message.role === 'assistant';
  const isUserWithAssistantResponse = previousMessage && previousMessage.role === 'user' && isAssistant;
  
  // Skip rendering user messages if the next message will combine them
  if (message.role === 'user') {
    return null;
  }
  
  // Determine success/failure status for assistant messages
  const getAssistantStatus = () => {
    if (!message.execution_results || message.execution_results.length === 0) {
      return { status: 'failure', text: 'Failed' };
    }
    
    const hasFailures = message.execution_results.some(result => !result.success);
    return hasFailures 
      ? { status: 'failure', text: 'Failed' }
      : { status: 'success', text: 'Success' };
  };

  // If it's an assistant message and toggle is off, show combined user+assistant header
  if (isAssistant && !showDetails) {
    const { status } = getAssistantStatus();
    
    return (
      <div key={keyPrefix} className={`${styles.message} ${styles.combined}`}>
        <div className={styles.messageHeader}>
          {sessionName && (
            <span className={styles.sessionName}>{sessionName}</span>
          )}
        </div>
        {/* Show user trigger content as clickable button */}
        {isUserWithAssistantResponse && previousMessage && (
          <div 
            className={`${styles.triggerContent} ${styles[status]}`}
            onClick={() => setShowDetails(!showDetails)}
            title="Show details"
          >
            {previousMessage.content}
          </div>
        )}
      </div>
    );
  }

  const { status } = getAssistantStatus();
  
  return (
    <div key={keyPrefix} className={`${styles.message} ${styles.combined}`}>
      <div className={styles.messageHeader}>
        {sessionName && (
          <span className={styles.sessionName}>{sessionName}</span>
        )}
      </div>
      
      {/* Show user trigger content as clickable button */}
      {isUserWithAssistantResponse && previousMessage && (
        <div 
          className={`${styles.triggerContent} ${styles[status]}`}
          onClick={() => setShowDetails(!showDetails)}
          title="Hide details"
        >
          {previousMessage.content}
        </div>
      )}
      
      {/* Show assistant response */}
      <div className={styles.responseContent}>
        {message.content}
      </div>
      
      {message.commands && message.commands.length > 0 && (
        <div className={styles.commands}>
          <strong>Commands:</strong>
          {message.commands.map((cmd, cmdIndex) => (
            <div key={cmdIndex} className={styles.command}>
              <code>{cmd.type}</code>
              <pre>{JSON.stringify(cmd.params, null, 2)}</pre>
            </div>
          ))}
        </div>
      )}
      
      {message.execution_results && message.execution_results.length > 0 && (
        <div className={styles.results}>
          <strong>Results:</strong>
          {message.execution_results.map((result, resultIndex) => (
            <div key={resultIndex} className={`${styles.result} ${result.success ? styles.success : styles.failure}`}>
              <div className={styles.resultHeader}>
                {result.command} - {result.success ? '✅ Success' : '❌ Failed'}
              </div>
              {result.success ? (
                <div>
                  <pre className={styles.resultData}>
                    {JSON.stringify(result.result, null, 2)}
                  </pre>
                  {/* Display screenshot if available */}
                  {result.result && typeof result.result === 'object' && 'image_url' in result.result && (
                    <div className={styles.screenshotContainer}>
                      <img 
                        src={result.result.image_url as string} 
                        alt="Screenshot" 
                        className={styles.screenshot}
                        onError={(e) => {
                          console.error('Failed to load screenshot:', result.result.image_url);
                          e.currentTarget.style.display = 'none';
                        }}
                      />
                    </div>
                  )}
                </div>
              ) : (
                <div className={styles.errorMessage}>{result.error}</div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}