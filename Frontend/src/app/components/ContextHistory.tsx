'use client';

import { useRef, forwardRef, useImperativeHandle, useEffect } from 'react';
import { SessionContext } from '../services';
import MessageItem from './MessageItem';
import styles from './ContextHistory.module.css';


interface ContextHistoryProps {
  context: SessionContext | null;
  loading: boolean;
  error: string | null;
  sessionsLoaded: boolean;
  sessionId: string | null;
}

export interface ContextHistoryRef {
  refreshContext: () => void;
}

const ContextHistory = forwardRef<ContextHistoryRef, ContextHistoryProps>(({ 
  context, 
  loading, 
  error, 
  sessionsLoaded, 
  sessionId 
}, ref) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Expose refresh function to parent component (now handled by parent)
  useImperativeHandle(ref, () => ({
    refreshContext: () => {
      // This will be handled by the parent component
      console.log('refreshContext called - handled by parent');
    }
  }), []);

  // Auto-scroll to bottom when context changes
  useEffect(() => {
    if (context && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [context]);


  if (!sessionsLoaded) {
    return (
      <div className={styles.container}>
        <div className={styles.loading}>Loading sessions...</div>
      </div>
    );
  }

  if (!sessionId) {
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
            {context.conversation_history
              .slice()
              .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
              .slice(-10) // Show only the last 1 message
              .map((message, index) => (
                <MessageItem
                  key={index}
                  message={message}
                  index={index}
                />
              ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>
    </div>
  );
});

ContextHistory.displayName = 'ContextHistory';

export default ContextHistory;