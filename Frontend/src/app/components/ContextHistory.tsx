'use client';

import { useState, useEffect, useRef, forwardRef, useImperativeHandle } from 'react';
import { useSessionStore } from '../store/sessionStore';
import { ApiService, Session, SessionContext } from '../services';
import MessageItem from './MessageItem';
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

interface ContextHistoryProps {
  apiService: ApiService;
}

export interface ContextHistoryRef {
  refreshContext: () => void;
}

const ContextHistory = forwardRef<ContextHistoryRef, ContextHistoryProps>(({ apiService }, ref) => {
  const [context, setContext] = useState<SessionContext | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { sessionId } = useSessionStore();
  
  // Context cache using useRef to persist across re-renders
  const contextCache = useRef<Map<string, SessionContext>>(new Map());
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Cache invalidation functions
  const invalidateSessionCache = (sessionId: string) => {
    contextCache.current.delete(sessionId);
  };
  
  const invalidateAllCache = () => {
    contextCache.current.clear();
  };

  // Expose refresh function to parent component
  useImperativeHandle(ref, () => ({
    refreshContext: () => {
      if (sessionId) {
        invalidateSessionCache(sessionId);
        fetchSessionContext(sessionId);
      }
    }
  }), [sessionId]);

  useEffect(() => {
    if (sessionId) {
      fetchSessionContext(sessionId);
    } else {
      setContext(null);
      setError(null);
    }
  }, [sessionId]);

  // Auto-scroll to bottom when context changes
  useEffect(() => {
    if (context && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [context]);

  const fetchSessionContext = async (id: string) => {
    // Check cache first
    const cachedContext = contextCache.current.get(id);
    if (cachedContext) {
      setContext(cachedContext);
      setError(null);
      return; // No loading state for cached data
    }

    setLoading(true);
    setError(null);

    try {
      const sessionContext = await apiService.fetchSessionContext(id);
      
      // Cache the result
      if (sessionContext) {
        contextCache.current.set(id, sessionContext);
      }
      
      setContext(sessionContext);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch session context');
      setContext(null);
    } finally {
      setLoading(false);
    }
  };


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
              .slice(-2) // Show only the last 1 message
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