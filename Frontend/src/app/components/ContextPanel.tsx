'use client';

import { useState, useRef, useEffect } from "react";
import { useSessionStore } from "../store/sessionStore";
import { createApiService, Session, SessionContext } from "../services";
import SessionController from "./SessionController";
import ContextHistory from "./ContextHistory";
import UnrealAIChat from "./UnrealAIChat";
import styles from "./ContextPanel.module.css";

export default function ContextPanel() {
  const { sessionId, setSessionId } = useSessionStore();
  const [error, setError] = useState<string | null>(null);
  
  // Centralized session management state
  const [sessionInfo, setSessionInfo] = useState<any[]>([]);
  const [sessionsLoaded, setSessionsLoaded] = useState(false);
  const [sessionsLoading, setSessionsLoading] = useState(true);
  
  // Session context state
  const [messageInfo, setMessageInfo] = useState<SessionContext | null>(null);
  const [contextLoading, setContextLoading] = useState(false);
  const [contextError, setContextError] = useState<string | null>(null);
  
  // Chat state
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);  
  const contextCache = useRef<Map<string, SessionContext>>(new Map());

  // Create API service with dependencies
  const apiService = createApiService(sessionId, setSessionId, setError);

  useEffect(() => {
    firstFetchSessions();
  }, []);

  const firstFetchSessions = async () => {
    setSessionsLoading(true);
    const sessionInfo = await updateSessionSelectorInfo();
    if (sessionInfo.length > 0 && !sessionId) {
		handleSessionSelect(sessionInfo[0].session_id);
	}
    setSessionsLoading(false);
    setSessionsLoaded(true);
  }

  const updateSessionSelectorInfo = async () => {
	const sessionInfo = await apiService.fetchSessionIds();
	setSessionInfo(sessionInfo);
	return sessionInfo;
  }

  const fetchSessionContext = async (id: string, forceRefresh = false) => {
    // Check cache first (unless forcing refresh)
    if (!forceRefresh) {
      const cachedContext = contextCache.current.get(id);
      if (cachedContext) {
        setMessageInfo(cachedContext);
        setContextError(null);
        return;
      }
    }

    if (!messageInfo || messageInfo.session_id !== id) {
      setContextLoading(true);
    }
    setContextError(null);

    try {
      const context = await apiService.fetchSessionContext(id);
      
      if (context) {
        contextCache.current.set(id, context);
      }
      
      setMessageInfo(context);
    } catch (err) {
      setContextError(err instanceof Error ? err.message : 'Failed to fetch session context');
      setMessageInfo(null);
    } finally {
      setContextLoading(false);
    }
  };

  const handleSessionSelect = async (selectedSessionId: string) => {
    setSessionId(selectedSessionId);
    const context = await apiService.fetchSessionContext(selectedSessionId);
    setMessageInfo(context);
  };

  const handleSessionCreate = async (sessionName: string) => {
    const result = await apiService.createSession(sessionName);
    await updateSessionSelectorInfo();
    if (result.session_id) {
      setSessionId(result.session_id);
	  handleSessionSelect(result.session_id);
    }
    return result;
  };

  const handleSessionDelete = async (sessionIdToDelete: string) => {
    await apiService.deleteSession(sessionIdToDelete);
    await updateSessionSelectorInfo();
    if (sessionId === sessionIdToDelete) {
      setSessionId(null);
	  firstFetchSessions();
    }
  };

  const handleChatSubmit = async (prompt: string, context: string, model?: string) => {
    setChatLoading(true);
    setChatError(null);

    try {
      const data = await apiService.sendMessage(prompt, context, model);
      
      // Refresh context after successful execution (with small delay to ensure DB update)
      if (sessionId) {
        contextCache.current.delete(sessionId);
        // Small delay to ensure database has been updated with model preference
        setTimeout(async () => {
          await fetchSessionContext(sessionId, true);
        }, 100);
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
        sessionInfo={sessionInfo}
        loading={sessionsLoading}
        error={error}
        activeSessionId={sessionId}
        onSessionSelect={handleSessionSelect}
        onSessionCreate={handleSessionCreate}
        onSessionDelete={handleSessionDelete}
      />
      <ContextHistory 
        context={messageInfo}
        loading={contextLoading}
        error={contextError}
        sessionsLoaded={sessionsLoaded}
      />
      <UnrealAIChat 
        loading={chatLoading}
        error={chatError}
        sessionId={sessionId}
        llmFromDb={messageInfo?.llm_model || 'gemini-2'}
        onSubmit={handleChatSubmit}
        onRefreshContext={refreshContext}
      />
    </div>
  );
}
