'use client';

import { useState, useRef, useEffect } from "react";
import { useSessionStore } from "../store/sessionStore";
import { createApiService, Session, SessionContext } from "../services";
import SessionSidebar from "./SessionSidebar";
import ConversationHistory from "./ConversationHistory";
import ChatInput from "./ChatInput";
import styles from "./SessionManagerPanel.module.css";

export default function SessionManagerPanel() {
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

  const apiService = createApiService();

  // Load all sessions on mount
  useEffect(() => {
    fetchSessions();
  }, []);

  // Load session context when sessionId changes
  useEffect(() => {
    if (sessionId) {
      fetchSessionContext(sessionId);
    } else {
      setMessageInfo(null);
    }
  }, [sessionId]);

  const fetchSessions = async () => {
    setSessionsLoading(true);
    try {
      const sessions = await apiService.getSessions();
      setSessionInfo(sessions);
      setSessionsLoaded(true);
    } catch (error) {
      console.error('Failed to fetch sessions:', error);
      setError('Failed to load sessions');
    } finally {
      setSessionsLoading(false);
    }
  };

  const fetchSessionContext = async (sid: string, forceRefresh: boolean = false) => {
    if (!forceRefresh && contextCache.current.has(sid)) {
      setMessageInfo(contextCache.current.get(sid)!);
      return;
    }

    setContextLoading(true);
    setContextError(null);
    try {
      const context = await apiService.getSessionContext(sid);
      contextCache.current.set(sid, context);
      setMessageInfo(context);
    } catch (error) {
      console.error('Failed to fetch session context:', error);
      setContextError('Failed to load conversation history');
    } finally {
      setContextLoading(false);
    }
  };

  const refreshContext = () => {
    if (sessionId) {
      contextCache.current.delete(sessionId);
      fetchSessionContext(sessionId, true);
    }
  };

  const handleChatSubmit = async (prompt: string, llmModel?: string) => {
    if (!sessionId || !prompt.trim()) return;

    setChatLoading(true);
    setChatError(null);

    try {
      const result = await apiService.chat(prompt, sessionId, llmModel);
      console.log('Chat result:', result);

      // Refresh context to show new messages
      contextCache.current.delete(sessionId);
      await fetchSessionContext(sessionId, true);

    } catch (error) {
      console.error('Chat error:', error);
      setChatError(error instanceof Error ? error.message : 'Chat failed');
    } finally {
      setChatLoading(false);
    }
  };

  const handleCreateSession = async (name: string) => {
    try {
      const session = await apiService.createSession(name);
      setSessionId(session.session_id);
      await fetchSessions(); // Refresh the list
      return session;
    } catch (error) {
      console.error('Failed to create session:', error);
      setError('Failed to create session');
      return null;
    }
  };

  const handleDeleteSession = async (sid: string) => {
    try {
      await apiService.deleteSession(sid);
      if (sessionId === sid) {
        setSessionId(null);
        setMessageInfo(null);
      }
      contextCache.current.delete(sid);
      await fetchSessions(); // Refresh the list
    } catch (error) {
      console.error('Failed to delete session:', error);
      setError('Failed to delete session');
    }
  };

  const handleRenameSession = async (sid: string, name: string) => {
    try {
      await apiService.renameSession(sid, name);
      await fetchSessions(); // Refresh the list
    } catch (error) {
      console.error('Failed to rename session:', error);
      setError('Failed to rename session');
    }
  };

  return (
    <div className={styles.container}>
      {error && (
        <div className={styles.error}>
          {error}
          <button onClick={() => setError(null)}>×</button>
        </div>
      )}
      <SessionSidebar 
        sessionInfo={sessionInfo}
        activeSessionId={sessionId}
        onSessionSelect={setSessionId}
        onSessionCreate={handleCreateSession}
        onSessionDelete={handleDeleteSession}
        onSessionRename={handleRenameSession}
        loading={sessionsLoading}
        error={error}
      />
      <ConversationHistory 
        context={messageInfo}
        loading={contextLoading}
        error={contextError}
        sessionsLoaded={sessionsLoaded}
      />
      <ChatInput 
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