'use client';

import styles from './ContextHistory.module.css';

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

  return (
    <div key={keyPrefix} className={`${styles.message} ${styles[message.role]}`}>
      <div className={styles.messageHeader}>
        <span className={styles.role}>{message.role.toUpperCase()}</span>
        {sessionName && (
          <span className={styles.sessionName}>{sessionName}</span>
        )}
        <span className={styles.timestamp}>
          {new Date(message.timestamp).toLocaleString()}
        </span>
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