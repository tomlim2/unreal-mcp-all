'use client';

import { useState, useRef, useEffect, ReactNode, useMemo, use } from "react";
import { useRouter } from "next/navigation";
import { createApiService, SessionContext, TransformRequest } from "../../services";
import { useSessionContext } from "../layout";
import { useSessionImagesStore } from "../../stores/sessionImagesStore";
import styles from "../../components/SessionManagerPanel.module.css";
import { ConversationContext, type ConversationContextType } from "./conversationContext";

// Conversation Provider Component
function ConversationProvider({
  children,
  sectionId
}: {
  children: ReactNode;
  sectionId: string;
}) {
  const router = useRouter();
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

  // Conversation context state
  const [messageInfo, setMessageInfo] = useState<SessionContext | null>(null);
  const [contextLoading, setContextLoading] = useState(false);
  const [contextError, setContextError] = useState<string | null>(null);

  // Chat state
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);
  const contextCache = useRef<Map<string, SessionContext>>(new Map());

  const apiService = useMemo(() => createApiService(), []);

  // Zustand store for session images
  const { setSessionImages, setLatestImage } = useSessionImagesStore();

  useEffect(() => {
    if (sectionId) {
      handleSelectSession(sectionId);
      
      if (!contextCache.current.has(sectionId) && messageInfo?.session_id !== sectionId) {
        fetchSessionContext(sectionId);
      } else if (contextCache.current.has(sectionId)) {
        setMessageInfo(contextCache.current.get(sectionId)!);
      }
    } else {
      setMessageInfo(null);
    }
  }, [sectionId]);

  const fetchSessionImages = async (sid: string) => {
    try {
      // Fetch latest image
      const latestImageResponse = await fetch(`http://localhost:8080/api/session/${sid}/latest-image`);
      if (latestImageResponse.ok) {
        const latestImageData = await latestImageResponse.json();
        setLatestImage(sid, latestImageData);
      }

      // Fetch session images
      const imagesResponse = await fetch(`http://localhost:8080/api/session/${sid}/images`);
      if (imagesResponse.ok) {
        const imagesData = await imagesResponse.json();
        setSessionImages(sid, imagesData.images || []);
      }
    } catch (error) {
      console.error('Failed to fetch session images:', error);
    }
  };

  const fetchSessionContext = async (sid: string, forceRefresh: boolean = false) => {
    if (!forceRefresh && contextCache.current.has(sid)) {
      setMessageInfo(contextCache.current.get(sid)!);
      return;
    }

    setContextError(null);
    setContextLoading(true);
    try {
      const context = await apiService.getSessionContext(sid);
      contextCache.current.set(sid, context);
      setMessageInfo(context);

      // Fetch and cache images
      await fetchSessionImages(sid);
    } catch (error) {
      console.error('Failed to fetch session context:', error);
      setContextError('Failed to load conversation history');
      // Redirect to /app if session doesn't exist
      router.replace('/app');
    } finally {
      setContextLoading(false);
    }
  };

  const refreshContext = () => {
    if (sectionId) {
      contextCache.current.delete(sectionId);
      fetchSessionContext(sectionId, true);
    }
  };

  const handleChatSubmit = async (prompt: string, llmModel?: string) => {
    if (!sectionId || !prompt.trim()) return;

    setChatLoading(true);
    setChatError(null);

    // Optimistically add user message to UI immediately
    if (messageInfo) {
      const optimisticMessage = {
        timestamp: new Date().toISOString(),
        role: 'user' as const,
        content: prompt.trim(),
      };

      setMessageInfo({
        ...messageInfo,
        conversation_history: [...messageInfo.conversation_history, optimisticMessage]
      });
    }

    try {
      const result = await apiService.chat(prompt, sectionId, llmModel);
      console.log('Chat result:', result);

      // Refresh context to show new messages
      contextCache.current.delete(sectionId);
      await fetchSessionContext(sectionId, true);

    } catch (error) {
      console.error('Chat error:', error);
      setChatError(error instanceof Error ? error.message : 'Chat failed');
      // Refresh to revert optimistic update on error
      contextCache.current.delete(sectionId);
      await fetchSessionContext(sectionId, true);
    } finally {
      setChatLoading(false);
    }
  };

  const handleTransformSubmit = async (data: Omit<TransformRequest, 'sessionId'> & { sessionId: string }) => {
    if (!sectionId) return;

    setChatLoading(true);
    setChatError(null);

    try {
      const result = await apiService.transform(data as TransformRequest);
      console.log('Transform result:', result);

      // Refresh context to show new messages
      contextCache.current.delete(sectionId);
      await fetchSessionContext(sectionId, true);

    } catch (error) {
      console.error('Transform error:', error);
      setChatError(error instanceof Error ? error.message : 'Transform failed');
    } finally {
      setChatLoading(false);
    }
  };

  // Wrap session operations to handle context cache
  const handleSessionDelete = async (sid: string) => {
    contextCache.current.delete(sid);
    await handleDeleteSession(sid);
  };

  const contextValue: ConversationContextType = {
    messageInfo,
    contextLoading,
    contextError,
    chatLoading,
    chatError,
    handleChatSubmit,
    handleTransformSubmit,
    refreshContext
  };

  return (
    <ConversationContext.Provider value={contextValue}>
      {error && (
        <div className={styles.error}>
          {error}
          <button onClick={() => setError(null)}>×</button>
        </div>
      )}
      {children}
    </ConversationContext.Provider>
  );
}

export default function SectionLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ 'section-id': string }>;
}) {
  const resolvedParams = use(params);
  
  return (
    <ConversationProvider sectionId={resolvedParams['section-id']}>
      {children}
    </ConversationProvider>
  );
}