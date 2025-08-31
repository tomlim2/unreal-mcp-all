'use client';

import { useState, useEffect, useRef } from 'react';
import { useSessionStore } from '../store/sessionStore';
import { ApiService, Session, SessionContext } from '../services';
import MessageItem from './MessageItem';
import styles from './ContextHistory.module.css';
import UnrealAIChat from './UnrealAIChat';

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

export default function ContextHistory({ apiService }: ContextHistoryProps) {
  const [context, setContext] = useState<SessionContext | null>(null);
  const [allSessions, setAllSessions] = useState<SessionContext[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { sessionId } = useSessionStore();
  
  // Context cache using useRef to persist across re-renders
  const contextCache = useRef<Map<string, SessionContext>>(new Map());
  const allSessionsCache = useRef<SessionContext[] | null>(null);
  
  // Cache invalidation functions
  const invalidateSessionCache = (sessionId: string) => {
    contextCache.current.delete(sessionId);
    allSessionsCache.current = null; // Clear all sessions cache too
  };
  
  const invalidateAllCache = () => {
    contextCache.current.clear();
    allSessionsCache.current = null;
  };
  
  // Force refresh function (for external use)
  const refreshCurrentView = () => {
    if (sessionId === 'all') {
      invalidateAllCache();
      fetchAllSessionsContext();
    } else if (sessionId) {
      invalidateSessionCache(sessionId);
      fetchSessionContext(sessionId);
    }
  };

  useEffect(() => {
    if (sessionId === 'all') {
      fetchAllSessionsContext();
    } else if (sessionId) {
      fetchSessionContext(sessionId);
    } else {
      setContext(null);
      setAllSessions([]);
      setError(null);
    }
  }, [sessionId]);

  const fetchSessionContext = async (id: string) => {
    // Check cache first
    const cachedContext = contextCache.current.get(id);
    if (cachedContext) {
      setContext(cachedContext);
      setAllSessions([]);
      setError(null);
      return; // No loading state for cached data
    }

    setLoading(true);
    setError(null);
    setAllSessions([]);

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

  const fetchAllSessionsContext = async () => {
    // Check if we have cached all sessions data
    if (allSessionsCache.current) {
      setAllSessions(allSessionsCache.current);
      setContext(null);
      setError(null);
      return; // No loading state for cached data
    }

    setLoading(true);
    setError(null);
    setContext(null);

    try {
      // First get list of sessions
      const sessions = await apiService.fetchSessions();
      const validContexts: SessionContext[] = [];

      // Use cached individual sessions where possible, fetch missing ones
      for (const session of sessions) {
        const cachedContext = contextCache.current.get(session.session_id);
        
        if (cachedContext) {
          // Use cached data
          validContexts.push(cachedContext);
        } else {
          // Fetch missing session context
          try {
            const sessionContext = await apiService.fetchSessionContext(session.session_id);
            
            if (sessionContext) {
              // Cache the newly fetched context
              contextCache.current.set(session.session_id, sessionContext);
              validContexts.push(sessionContext);
            }
          } catch {
            // If individual session fails, skip it
            continue;
          }
        }
      }
      
      // Cache the all sessions result
      allSessionsCache.current = validContexts;
      setAllSessions(validContexts);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch all sessions context');
      setAllSessions([]);
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

  // Show all sessions view - all conversations mixed by timestamp
  if (sessionId === 'all') {
    // Collect all messages from all sessions and sort by timestamp
    const allMessages: Array<ChatMessage & { sessionName: string; sessionId: string }> = [];
    
    allSessions.forEach(sessionContext => {
      sessionContext.conversation_history.forEach(message => {
        allMessages.push({
          ...message,
          sessionName: sessionContext.session_name || `Session ${sessionContext.session_id.slice(0, 8)}`,
          sessionId: sessionContext.session_id
        });
      });
    });

    // Sort all messages by timestamp
    allMessages.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());

    if (allMessages.length === 0 && !loading) {
      return (
        <div className={styles.container}>
          <h2>Context History - All Sessions</h2>
          <div className={styles.placeholder}>
            No conversations found across all sessions.
          </div>
        </div>
      );
    }

    return (
      <div className={styles.container}>
        <div className={styles.header}>
          <h2>Context History - All Sessions</h2>
          <button 
            className={styles.refreshButton} 
            onClick={refreshCurrentView}
            title="Refresh context data"
          >
            ↻
          </button>
        </div>
        <div className={styles.sessionInfo}>
          <h3>All Conversations (Chronological)</h3>
          <div className={styles.sessionMeta}>
            {allMessages.length} messages across {allSessions.length} sessions
          </div>
        </div>

        <div className={styles.section}>
          <h4>Conversation Timeline</h4>
          <div className={styles.messages}>
            {allMessages.map((message, index) => (
              <MessageItem
                key={`${message.sessionId}-${index}`}
                message={message}
                sessionName={message.sessionName}
                index={index}
                sessionId={message.sessionId}
              />
            ))}
          </div>
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
            {context.conversation_history
              .slice()
              .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
              .map((message, index) => (
                <MessageItem
                  key={index}
                  message={message}
                  index={index}
                />
              ))}
          </div>
        )}
      </div>

      {/* Scene State */}
      <div className={styles.section}>
        <h4>Scene State</h4>
        <div className={styles.sceneState}>
          {context.scene_state.lights.length > 0 && (
            <div className={styles.sceneItem}>
              <strong>Lights ({context.scene_state.lights.length}):</strong>
              {context.scene_state.lights.map((light, index) => (
                <div key={index} className={styles.lightItem}>
                  {light.name} - {light.light_type} (Intensity: {light.intensity})
                </div>
              ))}
            </div>
          )}
          
          {context.scene_state.cesium_location && (
            <div className={styles.sceneItem}>
              <strong>Location:</strong> Lat: {context.scene_state.cesium_location.latitude}, 
              Lng: {context.scene_state.cesium_location.longitude}
            </div>
          )}
          
          {Object.keys(context.scene_state.sky_settings).length > 0 && (
            <div className={styles.sceneItem}>
              <strong>Sky Settings:</strong>
              <pre>{JSON.stringify(context.scene_state.sky_settings, null, 2)}</pre>
            </div>
          )}
        </div>
      </div>
      {<UnrealAIChat apiService={apiService} />}
    </div>
  );
}