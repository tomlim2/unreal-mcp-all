'use client';

import { useState, useRef, useEffect } from "react";
import { createApiService, SessionContext } from "../services";
import { useSessionContext } from "../layout";
import Sidebar from "./sidebar/Sidebar";
import ConversationHistory from "./conversation/ConversationHistory";
import ChatInput, { ChatInputHandle } from "./chat/ChatInput";
import styles from "./SessionManagerPanel.module.css";

export default function SessionManagerPanel() {
  // Use session context from layout
  const {
    sessionInfo,
    sessionsLoaded,
    sessionsLoading,
    sessionId,
    handleCreateSession,
    handleDeleteSession,
    handleRenameSession,
    handleSelectSession,
    error,
    setError
  } = useSessionContext();
  
  // Session context state
  const [messageInfo, setMessageInfo] = useState<SessionContext | null>(null);
  const [contextLoading, setContextLoading] = useState(false);
  const [contextError, setContextError] = useState<string | null>(null);
  
  // Chat state
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);  
  const contextCache = useRef<Map<string, SessionContext>>(new Map());
  const chatInputRef = useRef<ChatInputHandle>(null);

  const apiService = createApiService();

  // Load session context when sessionId changes
  useEffect(() => {
    if (sessionId) {
      fetchSessionContext(sessionId);
    } else {
      setMessageInfo(null);
    }
  }, [sessionId]); // fetchSessionContext is stable, doesn't need to be in deps

  const fetchSessionContext = async (sid: string, forceRefresh: boolean = false) => {
    if (!forceRefresh && contextCache.current.has(sid)) {
      setMessageInfo(contextCache.current.get(sid)!);
      return;
    }

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

      // Focus back to input after response is received
      setTimeout(() => {
        chatInputRef.current?.focusInput();
      }, 100);

    } catch (error) {
      console.error('Chat error:', error);
      setChatError(error instanceof Error ? error.message : 'Chat failed');
    } finally {
      setChatLoading(false);
    }
  };

  // Wrap session operations to handle context cache
  const handleSessionDelete = async (sid: string) => {
    contextCache.current.delete(sid);
    await handleDeleteSession(sid);
  };

  const handleSessionSelect = (sid: string) => {
    handleSelectSession(sid);
  };

  return (
    <div className={styles.container}>
      {error && (
        <div className={styles.error}>
          {error}
          <button onClick={() => setError(null)}>×</button>
        </div>
      )}
      <Sidebar 
        sessionInfo={sessionInfo}
        activeSessionId={sessionId}
        onSessionDelete={handleSessionDelete}
        loading={chatLoading}
      />
      <ConversationHistory 
        context={messageInfo}
        loading={contextLoading}
        error={contextError}
        sessionsLoaded={sessionsLoaded}
      />
      <ChatInput 
        ref={chatInputRef}
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