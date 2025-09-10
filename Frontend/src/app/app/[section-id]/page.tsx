'use client';

import { use, useRef, useEffect } from "react";
import ChatInput, { ChatInputHandle } from "../../components/chat/ChatInput";
import ConversationHistory from "../../components/conversation/ConversationHistory";
import { useConversationContext } from "./layout";

export default function SectionPage({
  params,
}: {
  params: Promise<{ 'section-id': string }>;
}) {
  const resolvedParams = use(params);
  const chatInputRef = useRef<ChatInputHandle>(null);
  
  const {
    messageInfo,
    contextError,
    chatLoading,
    chatError,
    handleChatSubmit,
    refreshContext
  } = useConversationContext();

  // Force focus on page load
  useEffect(() => {
    const timer = setTimeout(() => {
      chatInputRef.current?.focusInput();
    }, 200);
    return () => clearTimeout(timer);
  }, []);
  return (
    <>
      <ConversationHistory 
        context={messageInfo}
        error={contextError}
        isNewSessionPage={false}
      />
      <ChatInput 
        ref={chatInputRef}
        loading={chatLoading}
        error={chatError}
        sessionId={resolvedParams['section-id']}
        llmFromDb={messageInfo?.llm_model || 'gemini-2'}
        onSubmit={handleChatSubmit}
        onRefreshContext={refreshContext}
      />
    </>
  );
}