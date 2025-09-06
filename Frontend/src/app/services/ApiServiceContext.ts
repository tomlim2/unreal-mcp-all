import { ApiService, Session, AIResponse, SessionContext } from './types';

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
    }
  };
}