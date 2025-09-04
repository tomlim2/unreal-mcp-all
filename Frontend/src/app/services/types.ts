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

// Job Management Types
export interface Job {
  job_id: string;
  job_type: 'screenshot' | 'batch_screenshot';
  status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
  progress?: number;
  result?: {
    filename?: string;
    file_path?: string;
    file_size?: number;
    thumbnail_url?: string;
    download_url?: string;
  };
  error?: string;
  metadata?: {
    original_prompt?: string;
    parameters?: Record<string, unknown>;
  };
}

export interface JobResponse {
  success: boolean;
  job_id?: string;
  job?: Job;
  error?: string;
}

// API Service Interface
export interface ApiService {
  // Session management
  fetchSessions: () => Promise<Session[]>;
  fetchSessionIds: () => Promise<any[]>;
  fetchSessionDetails: (sessionId: string) => Promise<Session>;
  createSession: (sessionName: string) => Promise<{ session_id: string; session_name: string }>;
  deleteSession: (sessionId: string) => Promise<void>;
  
  // Chat functionality
  sendMessage: (prompt: string, context?: string, model?: string) => Promise<AIResponse>;
  
  // Context history
  fetchSessionContext: (sessionId: string) => Promise<SessionContext>;

  // Job management
  startScreenshotJob: (parameters?: Record<string, unknown>) => Promise<JobResponse>;
  getJobStatus: (jobId: string) => Promise<Job>;
  getJobResult: (jobId: string) => Promise<Job>;
}