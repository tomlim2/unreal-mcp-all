'use client';

import { useState } from 'react';
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
}

export default function MessageItem({ message, sessionName, index, sessionId }: MessageItemProps) {
  const keyPrefix = sessionId ? `${sessionId}-${index}` : index;
  const [showAssistant, setShowAssistant] = useState(false);

  const isAssistant = message.role === 'assistant';
  
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

  // If it's an assistant message and toggle is off, show only the header with status and toggle button
  if (isAssistant && !showAssistant) {
    const { status, text } = getAssistantStatus();
    
    return (
      <div key={keyPrefix} className={`${styles.message} ${styles[message.role]}`}>
        <div className={styles.messageHeader}>
          <span className={styles.role}>{message.role.toUpperCase()}</span>
          {sessionName && (
            <span className={styles.sessionName}>{sessionName}</span>
          )}
          <span className={`${styles.status} ${styles[status]}`}>
            {status === 'success' ? '✅' : '❌'} {text}
          </span>
          <button
            onClick={() => setShowAssistant(!showAssistant)}
            className={styles.toggleButton}
            title="Show assistant message details"
          >
            ⬇
          </button>
        </div>
      </div>
    );
  }

  return (
    <div key={keyPrefix} className={`${styles.message} ${styles[message.role]}`}>
      <div className={styles.messageHeader}>
        <span className={styles.role}>{message.role.toUpperCase()}</span>
        {sessionName && (
          <span className={styles.sessionName}>{sessionName}</span>
        )}
{isAssistant && (
          <>
            <span className={`${styles.status} ${styles[getAssistantStatus().status]}`}>
              {getAssistantStatus().status === 'success' ? '✅' : '❌'} {getAssistantStatus().text}
            </span>
            <button
              onClick={() => setShowAssistant(!showAssistant)}
              className={styles.toggleButton}
              title="Hide assistant message"
            >
              ⬆
            </button>
          </>
        )}
      </div>
      <div className={styles.content}>{message.content}</div>
      
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
                <pre className={styles.resultData}>
                  {JSON.stringify(result.result, null, 2)}
                </pre>
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