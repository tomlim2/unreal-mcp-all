// API Types
export interface Session {
  session_id: string;
  session_name?: string;
  created_at: string;
  last_accessed: string;
  interaction_count?: number;
}

export interface AIResponse {
  explanation?: string;
  commands?: Array<{
    type: string;
    params: Record<string, unknown>;
  }>;
  expectedResult?: string;
  executionResults?: Array<{
    command: string;
    success: boolean;
    result?: unknown;
    error?: string;
  }>;
  error?: string;
  fallback?: boolean;
  session_id?: string;
}

export interface SessionContext {
  session_id: string;
  session_name: string;
  llm_model: 'gemini' | 'gemini-2' | 'claude';
  conversation_history: Array<{
    timestamp: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    commands?: Array<{
      type: string;
      params: Record<string, unknown>;
    }>;
    execution_results?: Array<{
      command: string;
      success: boolean;
      result?: unknown;
      error?: string;
    }>;
  }>;
  scene_state: {
    actors: Array<{
      name: string;
      type: string;
      location: { x: number; y: number; z: number };
      rotation: { x: number; y: number; z: number };
    }>;
    lights: Array<{
      name: string;
      light_type: string;
      intensity: number;
      color?: { r: number; g: number; b: number };
    }>;
    sky_settings: Record<string, unknown>;
    cesium_location?: { latitude: number; longitude: number };
    last_commands: unknown[];
    last_updated: string;
  };
  user_preferences: Record<string, unknown>;
  metadata: Record<string, unknown>;
  created_at: string;
  last_accessed: string;
}


// API Service Interface
export interface ApiService {
  // Session management
  getSessions: () => Promise<Session[]>;
  fetchSessionIds: () => Promise<string[]>;
  fetchSessionDetails: (sessionId: string) => Promise<Session>;
  createSession: (sessionName: string) => Promise<{ session_id: string; session_name: string }>;
  deleteSession: (sessionId: string) => Promise<void>;
  renameSession: (sessionId: string, name: string) => Promise<void>;
  
  // Chat functionality
  chat: (prompt: string, sessionId?: string, model?: string) => Promise<AIResponse>;
  
  // Context history
  getSessionContext: (sessionId: string) => Promise<SessionContext>;
}