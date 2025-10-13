'use client';

import { useRouter } from "next/navigation";
import { useMemo } from "react";
import ChatInput from "../components/chat/ChatInput";
import { useSessionContext } from "./layout";
import ConversationHistory from "../components/conversation/ConversationHistory";
import { createApiService } from "../services";
import type { CreateSessionWithImageRequest } from "../services";
import styles from "../components/SessionManagerPanel.module.css";

export default function AppHome() {
  const router = useRouter();
  const apiService = useMemo(() => createApiService(), []);
  const {
    handleCreateSession,
    fetchSessions,
    error,
    setError
  } = useSessionContext();

  const handleChatSubmit = async (prompt: string, llmModel?: string) => {
    if (!prompt.trim()) return;
    
    try {
      // Create new session with the first input as the session name
      const newSession = await handleCreateSession(prompt.trim());
      if (newSession) {
        // Send the prompt as the first message to the newly created session
        await apiService.chat(prompt.trim(), newSession.session_id, llmModel);
        
        // Redirect to the newly created session
        router.push(`/app/${newSession.session_id}`);
      }
    } catch (error) {
      console.error('Failed to create session and send first message:', error);
    }
  };

  const refreshContext = () => {
    // No context to refresh on /app page
    console.log('No context to refresh on /app page');
  };

  const handleTransformSubmit = async (data: Pick<CreateSessionWithImageRequest, 'prompt' | 'main_prompt' | 'reference_prompts' | 'model'> & { sessionId: string; mainImageData?: unknown; referenceImageData?: unknown }) => {
    try {
      // Call new atomic endpoint: create session + generate image
      const result = await apiService.createSessionWithImage({
        prompt: data.prompt,
        main_prompt: data.main_prompt,
        text_prompt: data.main_prompt || data.prompt,
        aspect_ratio: "16:9",
        model: data.model,
        mainImageData: ((): CreateSessionWithImageRequest['mainImageData'] => {
          const v = data.mainImageData as unknown;
          if (v && typeof v === 'object' && 'data' in (v as Record<string, unknown>) && 'mime_type' in (v as Record<string, unknown>)) {
            const r = v as { data: unknown; mime_type: unknown };
            if (typeof r.data === 'string' && typeof r.mime_type === 'string') {
              return { data: r.data, mime_type: r.mime_type };
            }
          }
          return undefined;
        })(),
        referenceImageData: ((): CreateSessionWithImageRequest['referenceImageData'] => {
          const arr = data.referenceImageData as unknown;
          if (Array.isArray(arr)) {
            const converted = arr
              .map((v) => {
                if (v && typeof v === 'object' && 'data' in (v as Record<string, unknown>) && 'mime_type' in (v as Record<string, unknown>)) {
                  const r = v as { data: unknown; mime_type: unknown };
                  if (typeof r.data === 'string' && typeof r.mime_type === 'string') {
                    return { data: r.data, mime_type: r.mime_type };
                  }
                }
                return undefined;
              })
              .filter((x): x is { data: string; mime_type: string } => Boolean(x));
            return converted.length > 0 ? converted : undefined;
          }
          return undefined;
        })(),
        reference_prompts: data.reference_prompts
      });

      if (result.success && result.session_id) {
        // Refresh session list to update sidebar
        await fetchSessions();

        // Redirect to the newly created session
        router.push(result.redirect_url || `/app/${result.session_id}`);
      }
    } catch (error) {
      console.error('Failed to create session with image:', error);
    }
  };

  return (
    <>
      {error && (
        <div className={styles.error}>
          {error}
          <button onClick={() => setError(null)}>×</button>
        </div>
      )}
      <ConversationHistory
        context={null}
        error={null}
        isNewSessionPage={true}
      />
      <ChatInput
        loading={false}
        error={null}
        sessionId={null}
        llmFromDb="gemini-2"
        onSubmit={handleChatSubmit}
        onTransformSubmit={handleTransformSubmit}
        onRefreshContext={refreshContext}
        allowModelSwitching={true}
      />
    </>
  );
}