'use client';

import { useEffect, useRef } from 'react';
import { SessionContext } from '../../services';
import { MessageItem } from './messages';
import styles from './ConversationHistory.module.css';

interface ConversationHistoryProps {
  context: SessionContext | null;
  error: string | null;
  isNewSessionPage?: boolean;
}

const ConversationHistory = ({
  context,
  error,
  isNewSessionPage = false,
}: ConversationHistoryProps) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const isFirstLoadRef = useRef<boolean>(true);
  const previousMessageCountRef = useRef<number>(0);

  const scrollToBottom = (instant = false) => {
    messagesEndRef.current?.scrollIntoView({
      behavior: instant ? 'auto' : 'smooth'
    });
  };

  // Reset first load flag when session changes
  useEffect(() => {
    isFirstLoadRef.current = true;
    previousMessageCountRef.current = 0;
  }, [context?.session_id]);

  useEffect(() => {
    if (context?.conversation_history) {
      const currentMessageCount = context.conversation_history.length;

      // Only scroll if:
      // 1. First load (instant scroll to bottom)
      // 2. New message added (message count increased)
      if (isFirstLoadRef.current) {
        scrollToBottom(true); // Instant scroll on first load
        isFirstLoadRef.current = false;
        previousMessageCountRef.current = currentMessageCount;
      } else if (currentMessageCount > previousMessageCountRef.current) {
        scrollToBottom(false); // Smooth scroll for new messages
        previousMessageCountRef.current = currentMessageCount;
      }
    }
  }, [context?.conversation_history]);

  if (!context?.session_id) {
    return (
      <div className={styles.container}>
        <div className={styles.placeholder}>
          {isNewSessionPage 
            ? "Start a new conversation by typing a message below."
            : ""
          }
        </div>
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
          <div className={styles.messages}>
            <div className={styles.spacer}></div>
          </div>
        ) : (
          <div className={styles.messages}>
            <div className={styles.spacer}></div>
            {context.conversation_history
              .slice()
              .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
              .map((message, index, allMessages) => (
                <MessageItem
                  key={`${context.session_id}-${index}`}
                  message={message}
                  index={index}
                  sessionId={context.session_id}
                  allMessages={allMessages}
                />
              ))
            }
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>
    </div>
  );
};

ConversationHistory.displayName = 'ConversationHistory';

export default ConversationHistory;