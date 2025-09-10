'use client';

import { useState, useRef, useEffect, createContext, useContext, ReactNode, useMemo, use } from "react";
import { createApiService, SessionContext } from "../../services";
import { useSessionContext } from "../layout";
import styles from "../../components/SessionManagerPanel.module.css";

// Conversation Context Types
interface ConversationContextType {
  // Conversation data
  messageInfo: SessionContext | null;
  contextLoading: boolean;
  contextError: string | null;
  
  // Chat state
  chatLoading: boolean;
  chatError: string | null;
  
  // Operations
  handleChatSubmit: (prompt: string, llmModel?: string) => Promise<void>;
  refreshContext: () => void;
}

// Create Conversation Context
const ConversationContext = createContext<ConversationContextType | null>(null);

// Custom hook to use conversation context
export const useConversationContext = () => {
  const context = useContext(ConversationContext);
  if (!context) {
    throw new Error('useConversationContext must be used within a ConversationProvider');
  }
  return context;
};

// Conversation Provider Component
function ConversationProvider({ 
  children, 
  sectionId 
}: { 
  children: ReactNode;
  sectionId: string;
}) {
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
    } catch (error) {
      console.error('Failed to fetch session context:', error);
      setContextError('Failed to load conversation history');
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

    try {
      const result = await apiService.chat(prompt, sectionId, llmModel);
      console.log('Chat result:', result);

      // Refresh context to show new messages
      contextCache.current.delete(sectionId);
      await fetchSessionContext(sectionId, true);

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

  const contextValue: ConversationContextType = {
    messageInfo,
    contextLoading,
    contextError,
    chatLoading,
    chatError,
    handleChatSubmit,
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