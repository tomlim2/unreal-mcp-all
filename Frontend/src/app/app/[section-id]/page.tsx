'use client';

import { use, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import ChatInput, { ChatInputHandle } from "../../components/chat/ChatInput";
import ConversationHistory from "../../components/conversation/ConversationHistory";
import { useConversationContext } from "./layout";

export default function SectionPage({
  params,
}: {
  params: Promise<{ 'section-id': string }>;
}) {
  const resolvedParams = use(params);
  const router = useRouter();
  const chatInputRef = useRef<ChatInputHandle>(null);
  
  const sectionId = resolvedParams['section-id'];
  
  const {
    messageInfo,
    contextError,
    chatLoading,
    chatError,
    handleChatSubmit,
    refreshContext
  } = useConversationContext();

  // Validate session ID and redirect if invalid
  useEffect(() => {
    if (!sectionId || sectionId.trim() === '') {
      console.log('No valid session ID provided, redirecting to /app');
      router.replace('/app');
      return;
    }
    
    // Force focus on page load after validation
    const timer = setTimeout(() => {
      chatInputRef.current?.focusInput();
    }, 200);
    return () => clearTimeout(timer);
  }, [sectionId, router]);
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
        sessionId={sectionId}
        llmFromDb={messageInfo?.llm_model || 'gemini-2'}
        onSubmit={handleChatSubmit}
        onRefreshContext={refreshContext}
      />
    </>
  );
}