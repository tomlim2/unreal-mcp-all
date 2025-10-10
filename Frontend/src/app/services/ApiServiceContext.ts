import { ApiService, Session, AIResponse, SessionContext, TransformRequest, CreateSessionWithImageRequest, CreateSessionWithImageResponse } from './types';

interface SessionsResponse {
  sessions: Session[];
  error?: string;
}

interface SessionIdsResponse {
  session_ids: string[];
  error?: string;
}

export function createApiService(): ApiService {
  return {
    getSessions: async (): Promise<Session[]> => {
      try {
        const response = await fetch("/api/sessions");
        const data: SessionsResponse = await response.json();
        
        if (data.error) {
          throw new Error(data.error);
        }
        
        return data.sessions || [];
      } catch (err) {
        console.error(err instanceof Error ? err.message : "Failed to fetch sessions");
        throw err;
      }
    },

    fetchSessionIds: async (): Promise<string[]> => {
      try {
        const response = await fetch("/api/session-ids");
        const data: SessionIdsResponse = await response.json();
        
        if (data.error) {
          throw new Error(data.error);
        }
        
        return data.session_ids || [];
      } catch (err) {
        console.error(err instanceof Error ? err.message : "Failed to fetch session IDs");
        throw err;
      }
    },

    fetchSessionDetails: async (sessionId: string): Promise<Session> => {
      try {
        const response = await fetch(`/api/sessions/${sessionId}`);
        const data = await response.json();
        
        if (data.error) {
          throw new Error(data.error);
        }
        
        return data;
      } catch (err) {
        console.error(err instanceof Error ? err.message : "Failed to fetch session details");
        throw err;
      }
    },

    createSession: async (sessionName: string) => {
      try {
        const response = await fetch("/api/sessions", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            session_name: sessionName.trim(),
          }),
        });

        if (!response.ok) {
          throw new Error(`Failed to create session: ${response.status}`);
        }

        const result = await response.json();

        if (result.error) {
          throw new Error(result.error);
        }

        return result;
      } catch (err) {
        console.error(err instanceof Error ? err.message : "Failed to create session");
        throw err;
      }
    },

    deleteSession: async (sessionId: string) => {
      try {
        const response = await fetch(`/api/sessions/${sessionId}`, {
          method: "DELETE",
        });

        if (!response.ok) {
          throw new Error(`Failed to delete session: ${response.status}`);
        }

        const result = await response.json();

        if (result.error) {
          throw new Error(result.error);
        }
      } catch (err) {
        console.error(err instanceof Error ? err.message : "Failed to delete session");
        throw err;
      }
    },

    chat: async (prompt: string, sessionId?: string, model?: string): Promise<AIResponse> => {
      try {
        const requestBody: Record<string, unknown> = {
          prompt,
          context: 'User is working with Unreal Engine project with dynamic sky system',
          llm_model: model
        };
        
        // Include session ID if we have one
        if (sessionId) {
          requestBody.session_id = sessionId;
        }
        
        const response = await fetch('/api/mcp', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(requestBody),
        });

        if (!response.ok) {
          throw new Error('Failed to get AI response');
        }

        const data: AIResponse = await response.json();
        return data;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'An error occurred';
        console.error(errorMessage);
        throw err;
      }
    },

    getSessionContext: async (sessionId: string): Promise<SessionContext> => {
      try {
        const response = await fetch(`/api/sessions/${sessionId}/context`);
        
        if (!response.ok) {
          throw new Error(`Failed to fetch session context: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.error) {
          throw new Error(data.error);
        }
        
        return data.context;
      } catch (err) {
        console.error(err instanceof Error ? err.message : "Failed to fetch session context");
        throw err;
      }
    },

    renameSession: async (sessionId: string, name: string) => {
      try {
        const response = await fetch(`/api/sessions/${sessionId}/name`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ session_name: name }),
        });

        if (!response.ok) {
          throw new Error(`Failed to rename session: ${response.status}`);
        }

        const result = await response.json();
        if (result.error) {
          throw new Error(result.error);
        }
      } catch (err) {
        console.error(err instanceof Error ? err.message : "Failed to rename session");
        throw err;
      }
    },

    transform: async (data: TransformRequest): Promise<AIResponse> => {
      try {
        // Prepare request body
        const requestBody: Record<string, any> = {
          prompt: data.prompt,
          context: 'User is working with Unreal Engine project with dynamic sky system',
          llm_model: data.model,
          session_id: data.sessionId,
        };

        // Add new enhanced prompt fields
        if (data.main_prompt) {
          requestBody.main_prompt = data.main_prompt;
        }
        if (data.reference_prompts && data.reference_prompts.length > 0) {
          requestBody.reference_prompts = data.reference_prompts;
        }

        // Add main image - either uploaded or from UID
        if (data.mainImageData) {
          // User-uploaded main image
          requestBody.mainImageData = data.mainImageData;
        } else if (data.sessionId) {
          // Try to fetch latest image UID from session
          try {
            const latestImageResponse = await fetch(`http://127.0.0.1:8080/api/session/${data.sessionId}/latest-image`);
            const latestImageData = await latestImageResponse.json();

            if (latestImageData.success && latestImageData.latest_image.uid) {
              requestBody.target_image_uid = latestImageData.latest_image.uid;
            }
          } catch (err) {
            console.warn('Could not fetch latest image, will use uploaded image if provided:', err);
          }
        }

        console.log('API Service: Sending transform request with enhanced prompts:', {
          prompt: data.prompt,
          main_prompt: data.main_prompt,
          reference_prompts: data.reference_prompts,
          mainImageData: data.mainImageData ? 'present' : 'none',
          referenceImageData: data.referenceImageData?.length || 0
        });

        // Add reference images directly (no UID storage)
        if (data.referenceImageData && data.referenceImageData.length > 0) {
          requestBody.referenceImageData = data.referenceImageData;
          console.log('API Service: Added referenceImageData to requestBody, count:', data.referenceImageData.length);
        } else {
          console.log('API Service: NO referenceImageData to add', { hasData: !!data.referenceImageData, length: data.referenceImageData?.length });
        }

        const response = await fetch('/api/mcp', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(requestBody),
        });

        if (!response.ok) {
          throw new Error('Failed to transform image');
        }

        const result: AIResponse = await response.json();
        return result;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Transform failed';
        console.error(errorMessage);
        throw err;
      }
    },

    createSessionWithImage: async (data: CreateSessionWithImageRequest): Promise<CreateSessionWithImageResponse> => {
      try {
        const httpBridgePort = process.env.NEXT_PUBLIC_HTTP_BRIDGE_PORT || '8080';
        const response = await fetch(`http://localhost:${httpBridgePort}/api/create-session-with-image`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(data),
        });

        if (!response.ok) {
          throw new Error(`Failed to create session with image: ${response.status}`);
        }

        const result: CreateSessionWithImageResponse = await response.json();

        if (!result.success) {
          throw new Error(result['error'] || 'Failed to create session with image');
        }

        return result;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Create session with image failed';
        console.error(errorMessage);
        throw err;
      }
    }
  };
}