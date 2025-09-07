'use client';

import ChatInput from "../../components/ChatInput";
import { useConversationContext } from "./layout";

export default function SectionPage({
  params,
}: {
  params: { 'section-id': string };
}) {
  const {
    messageInfo,
    chatLoading,
    chatError,
    handleChatSubmit,
    refreshContext
  } = useConversationContext();

  return (
    <ChatInput 
      loading={chatLoading}
      error={chatError}
      sessionId={params['section-id']}
      llmFromDb={messageInfo?.llm_model || 'gemini-2'}
      onSubmit={handleChatSubmit}
      onRefreshContext={refreshContext}
    />
  );
}