import { ApiService, Session, AIResponse, SessionContext } from './types';

interface SessionsResponse {
  sessions: Session[];
  error?: string;
}

interface SessionIdsResponse {
  session_ids: string[];
  error?: string;
}

export function createApiService(
  sessionId: string | null,
  setSessionId: (sessionId: string | null) => void,
  setError: (error: string | null) => void
): ApiService {
  return {
    fetchSessions: async (): Promise<Session[]> => {
      try {
        const response = await fetch("/api/sessions");
        const data: SessionsResponse = await response.json();
        
        if (data.error) {
          throw new Error(data.error);
        }
        
        return data.sessions || [];
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch sessions");
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
        setError(err instanceof Error ? err.message : "Failed to fetch session IDs");
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
        setError(err instanceof Error ? err.message : "Failed to fetch session details");
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
        setError(err instanceof Error ? err.message : "Failed to create session");
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
        setError(err instanceof Error ? err.message : "Failed to delete session");
        throw err;
      }
    },

    sendMessage: async (prompt: string, context?: string): Promise<AIResponse> => {
      try {
        setError(null);
        
        const requestBody: Record<string, unknown> = {
          prompt,
          context: context || 'User is working with Unreal Engine project with dynamic sky system'
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
        
        // Only update session ID if we got a successful response with a session_id
        // and we don't have a specific session selected
        if (data.session_id && !data.error && !sessionId) {
          setSessionId(data.session_id);
        }
        
        return data;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'An error occurred';
        setError(errorMessage);
        
        // Clear session ID if backend is unavailable
        if (err instanceof Error && (err.message.includes('Failed to fetch') || err.message.includes('Failed to get AI response'))) {
          setSessionId(null); // Clear session when backend is down
        }
        
        throw err;
      }
    },

    fetchSessionContext: async (sessionId: string): Promise<SessionContext> => {
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
        setError(err instanceof Error ? err.message : "Failed to fetch session context");
        throw err;
      }
    }
  };
}