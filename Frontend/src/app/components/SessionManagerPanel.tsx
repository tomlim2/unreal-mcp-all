'use client';

import { useState, useRef, useEffect } from "react";
import { createApiService, SessionContext, TransformRequest, Session } from "../services";
import { useSessionImagesStore } from "../stores/sessionImagesStore";
import Sidebar from "./sidebar/Sidebar";
import ConversationHistory from "./conversation/ConversationHistory";
import ChatInput, { ChatInputHandle } from "./chat/ChatInput";
import styles from "./SessionManagerPanel.module.css";

export default function SessionManagerPanel() {
  // Use session context from layout
  // Local fallbacks (component can operate standalone without global session provider)
  const sessionInfo: Session[] = [];
  const sessionId: string | null = null;
  const handleDeleteSession = async (_sid: string) => {};
  const handleSelectSession = (_sid: string) => {};
  const [error, setError] = useState<string | null>(null);

  // Session images store
  const { invalidateSession } = useSessionImagesStore();

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

      // Invalidate session images cache (new screenshot may have been taken)
      invalidateSession(sessionId);

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
    invalidateSession(sid); // Clear session images cache
    await handleDeleteSession(sid);
  };

  const handleSessionSelect = (sid: string) => {
    handleSelectSession(sid);
  };

  const handleTransformSubmit = async (data: Omit<TransformRequest, 'sessionId'> & { sessionId: string }) => {
    if (!sessionId) return;

    setChatLoading(true);
    setChatError(null);

    try {
      const result = await apiService.transform(data as TransformRequest);
      console.log('Transform result:', result);

      // Invalidate session images cache (new transformed image was created)
      invalidateSession(sessionId);

      // Refresh context to show new messages
      contextCache.current.delete(sessionId);
      await fetchSessionContext(sessionId, true);

      // Focus back to input after response is received
      setTimeout(() => {
        chatInputRef.current?.focusInput();
      }, 100);

    } catch (error) {
      console.error('Transform error:', error);
      setChatError(error instanceof Error ? error.message : 'Transform failed');
    } finally {
      setChatLoading(false);
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
      <Sidebar 
        sessionInfo={sessionInfo}
        activeSessionId={sessionId ?? null}
        onSessionDelete={handleSessionDelete}
        loading={chatLoading}
      />
      <ConversationHistory 
        context={messageInfo}
        error={contextError}
      />
      <ChatInput
        ref={chatInputRef}
        loading={chatLoading}
        error={chatError}
        sessionId={sessionId ?? null}
        llmFromDb={messageInfo?.llm_model || 'gemini-2'}
        onSubmit={handleChatSubmit}
        onTransformSubmit={handleTransformSubmit}
        onRefreshContext={refreshContext}
      />
    </div>
  );
}