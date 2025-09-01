'use client';

import { useState, useRef, useEffect } from "react";
import { useSessionStore } from "../store/sessionStore";
import { createApiService, Session, SessionContext } from "../services";
import SessionController from "./SessionController";
import ContextHistory, { ContextHistoryRef } from "./ContextHistory";
import UnrealAIChat from "./UnrealAIChat";
import styles from "./ContextPanel.module.css";

export default function ContextPanel() {
  const { sessionId, setSessionId } = useSessionStore();
  const [error, setError] = useState<string | null>(null);
  
  // Centralized session management state
  const [sessionIds, setSessionIds] = useState<string[]>([]);
  const [sessionDetails, setSessionDetails] = useState<Map<string, Session>>(new Map());
  const [sessionsLoaded, setSessionsLoaded] = useState(false);
  const [sessionsLoading, setSessionsLoading] = useState(true);
  
  // Session context state
  const [sessionContext, setSessionContext] = useState<SessionContext | null>(null);
  const [contextLoading, setContextLoading] = useState(false);
  const [contextError, setContextError] = useState<string | null>(null);
  
  // Chat state
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);
  
  const contextHistoryRef = useRef<ContextHistoryRef>(null);
  const contextCache = useRef<Map<string, SessionContext>>(new Map());

  // Create API service with dependencies
  const apiService = createApiService(sessionId, setSessionId, setError);

  // Computed sessions array from IDs and details
  const sessions: Session[] = sessionIds.map(id => {
    const details = sessionDetails.get(id);
    if (details) {
      return details;
    }
    // Return minimal session if details not loaded yet
    return {
      session_id: id,
      session_name: undefined,
      created_at: '',
      last_accessed: '',
      interaction_count: 0
    };
  });

  // Load sessions on component mount
  useEffect(() => {
    fetchSessions(true);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Load session context when sessionId changes
  useEffect(() => {
    if (sessionsLoaded && sessionId) {
      fetchSessionContext(sessionId);
    } else {
      setSessionContext(null);
      setContextError(null);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId, sessionsLoaded]);

  const fetchSessions = async (isInitialLoad = false) => {
    try {
      if (isInitialLoad) {
        setSessionsLoading(true);
      }
      setError(null);

      // Phase 1: Get session IDs quickly
      const ids = await apiService.fetchSessionIds();
      setSessionIds(ids);
      console.log('ContextPanel loaded session IDs:', ids.length);
      
      setSessionsLoaded(true);
      
      // Phase 2: Load details for visible/important sessions in background
      await loadSessionDetails(ids.slice(0, 10));
      
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch sessions");
      setSessionsLoaded(false);
    } finally {
      if (isInitialLoad) {
        setSessionsLoading(false);
      }
    }
  };

  const loadSessionDetails = async (idsToLoad: string[]) => {
    const detailsMap = new Map(sessionDetails);
    
    const promises = idsToLoad
      .filter(id => !detailsMap.has(id))
      .map(async (id) => {
        try {
          const details = await apiService.fetchSessionDetails(id);
          return { id, details };
        } catch (err) {
          console.warn(`Failed to load details for session ${id}:`, err);
          return null;
        }
      });
    
    const results = await Promise.all(promises);
    
    results.forEach(result => {
      if (result) {
        detailsMap.set(result.id, result.details);
      }
    });
    
    setSessionDetails(detailsMap);
  };

  const fetchSessionContext = async (id: string, forceRefresh = false) => {
    // Check cache first (unless forcing refresh)
    if (!forceRefresh) {
      const cachedContext = contextCache.current.get(id);
      if (cachedContext) {
        setSessionContext(cachedContext);
        setContextError(null);
        return;
      }
    }

    if (!sessionContext || sessionContext.session_id !== id) {
      setContextLoading(true);
    }
    setContextError(null);

    try {
      const context = await apiService.fetchSessionContext(id);
      
      if (context) {
        contextCache.current.set(id, context);
      }
      
      setSessionContext(context);
    } catch (err) {
      setContextError(err instanceof Error ? err.message : 'Failed to fetch session context');
      setSessionContext(null);
    } finally {
      setContextLoading(false);
    }
  };

  const handleSessionSelect = async (selectedSessionId: string) => {
    setSessionId(selectedSessionId);
    
    // Load details for selected session if not already loaded
    if (!sessionDetails.has(selectedSessionId)) {
      await loadSessionDetails([selectedSessionId]);
    }
  };

  const handleSessionCreate = async (sessionName: string) => {
    const result = await apiService.createSession(sessionName);
    await fetchSessions(false);
    
    if (result.session_id) {
      setSessionId(result.session_id);
    }
    
    return result;
  };

  const handleSessionDelete = async (sessionIdToDelete: string) => {
    await apiService.deleteSession(sessionIdToDelete);
    
    if (sessionId === sessionIdToDelete) {
      setSessionId(null);
    }
    
    await fetchSessions(false);
  };

  const handleChatSubmit = async (prompt: string, context: string) => {
    setChatLoading(true);
    setChatError(null);

    try {
      const data = await apiService.sendMessage(prompt, context);
      
      // Refresh context after successful execution
      if (sessionId) {
        contextCache.current.delete(sessionId);
        await fetchSessionContext(sessionId, true);
      }
      
      return data;
    } catch (err) {
      const error = err instanceof Error ? err.message : "An error occurred";
      setChatError(error);
      throw err;
    } finally {
      setChatLoading(false);
    }
  };

  const refreshContext = () => {
    if (sessionId) {
      contextCache.current.delete(sessionId);
      fetchSessionContext(sessionId, true);
    }
  };

  return (
    <div className={styles.contextPanel}>
      {error && (
        <div className={styles.globalError}>
          <span>⚠️ {error}</span>
          <button onClick={() => setError(null)}>×</button>
        </div>
      )}
      <SessionController 
        sessions={sessions}
        loading={sessionsLoading}
        error={error}
        activeSessionId={sessionId}
        onSessionSelect={handleSessionSelect}
        onSessionCreate={handleSessionCreate}
        onSessionDelete={handleSessionDelete}
        onRefresh={() => fetchSessions(false)}
      />
      <ContextHistory 
        ref={contextHistoryRef}
        context={sessionContext}
        loading={contextLoading}
        error={contextError}
        sessionsLoaded={sessionsLoaded}
        sessionId={sessionId}
      />
      <UnrealAIChat 
        loading={chatLoading}
        error={chatError}
        sessionId={sessionId}
        onSubmit={handleChatSubmit}
        onRefreshContext={refreshContext}
      />
    </div>
  );
}
