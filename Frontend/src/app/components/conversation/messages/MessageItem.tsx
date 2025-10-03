'use client';

import React from 'react';
import styles from './MessageItem.module.css';
import AssistantMessage from './AssistantMessage';

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
  allMessages?: ChatMessage[];
}

export default function MessageItem({ message, sessionName, index, sessionId, allMessages }: MessageItemProps) {
  const keyPrefix = sessionId ? `${sessionId}-${index}` : index;

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
    return (
      <AssistantMessage
        message={message}
        sessionName={sessionName}
        keyPrefix={keyPrefix}
        sessionId={sessionId}
        allMessages={allMessages}
        currentIndex={index}
      />
    );
  }
  return null;
}