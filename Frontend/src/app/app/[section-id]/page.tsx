'use client';

import { use } from "react";
import ChatInput from "../../components/chat/ChatInput";
import ConversationHistory from "../../components/conversation/ConversationHistory";
import { useConversationContext } from "./layout";

export default function SectionPage({
  params,
}: {
  params: Promise<{ 'section-id': string }>;
}) {
  const resolvedParams = use(params);
  const {
    messageInfo,
    contextError,
    chatLoading,
    chatError,
    handleChatSubmit,
    refreshContext
  } = useConversationContext();
  return (
    <>
      <ConversationHistory 
        context={messageInfo}
        error={contextError}
        isNewSessionPage={false}
      />
      <ChatInput 
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