'use client';

import { createContext, useContext } from 'react';
import type { SessionContext, TransformRequest } from '../../services';

// Conversation Context Types
export interface ConversationContextType {
  // Conversation data
  messageInfo: SessionContext | null;
  contextLoading: boolean;
  contextError: string | null;

  // Chat state
  chatLoading: boolean;
  chatError: string | null;

  // Operations
  handleChatSubmit: (prompt: string, llmModel?: string) => Promise<void>;
  handleTransformSubmit: (data: Omit<TransformRequest, 'sessionId'> & { sessionId: string }) => Promise<void>;
  refreshContext: () => void;
}

// Create Conversation Context
export const ConversationContext = createContext<ConversationContextType | null>(null);

// Custom hook to use conversation context
export const useConversationContext = () => {
  const context = useContext(ConversationContext);
  if (!context) {
    throw new Error('useConversationContext must be used within a ConversationProvider');
  }
  return context;
};
