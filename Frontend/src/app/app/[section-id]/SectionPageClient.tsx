'use client';

import { useRef, useEffect } from 'react';
import ChatInput, { ChatInputHandle } from '../../components/chat/ChatInput';
import ConversationHistory from '../../components/conversation/ConversationHistory';
import { useConversationContext } from './conversationContext';

export default function SectionPageClient({ sectionId }: { sectionId: string }) {
  const chatInputRef = useRef<ChatInputHandle>(null);

  const {
    messageInfo,
    contextError,
    chatLoading,
    chatError,
    handleChatSubmit,
    handleTransformSubmit,
    refreshContext,
  } = useConversationContext();

  useEffect(() => {
    const timer = setTimeout(() => {
      chatInputRef.current?.focusInput();
    }, 200);
    return () => clearTimeout(timer);
  }, []);

  return (
    <>
      <ConversationHistory context={messageInfo} error={contextError} isNewSessionPage={false} />
      <ChatInput
        ref={chatInputRef}
        loading={chatLoading}
        error={chatError}
        sessionId={sectionId}
        llmFromDb={messageInfo?.llm_model || 'gemini-2'}
        onSubmit={handleChatSubmit}
        onTransformSubmit={handleTransformSubmit}
        onRefreshContext={refreshContext}
        allowModelSwitching={false}
      />
    </>
  );
}
