'use client';

import { useEffect, useRef } from 'react';
import { SessionContext } from '../services';
import { MessageItem, MessageGroupWrapper } from './messages';
import styles from './ConversationHistory.module.css';

interface ConversationHistoryProps {
  context: SessionContext | null;
  loading: boolean;
  error: string | null;
  sessionsLoaded: boolean;
}

const ConversationHistory = ({ 
  context, 
  loading, 
  error, 
  sessionsLoaded, 
}: ConversationHistoryProps) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [context?.conversation_history]);
  if (!sessionsLoaded) {
    return (
      <div className={styles.container}>
        <div className={styles.loading}>Loading sessions...</div>
      </div>
    );
  }

  if (!context?.session_id) {
    return (
      <div className={styles.container}>
        <div className={styles.placeholder}>
          Select a session to view its context and conversation history.
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className={styles.container}>
        <div className={styles.loading}>Loading context...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.container}>
        <div className={styles.error}>
          Error: {error}
        </div>
      </div>
    );
  }

  // Single session view
  if (!context) {
    return (
      <div className={styles.container}>
        <div className={styles.placeholder}>
          No context data found for this session.
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      {/* Conversation History */}
      <div className={styles.section}>
        {context.conversation_history.length === 0 ? (
          <div className={styles.empty}>No conversation history yet.</div>
        ) : (
          <div className={styles.messages}>
            <div className={styles.spacer}></div>
            <MessageGroupWrapper
              messages={context.conversation_history
                .slice()
                .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
              }
              sessionId={context.session_id}
            />
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>
    </div>
  );
};

ConversationHistory.displayName = 'ConversationHistory';

export default ConversationHistory;