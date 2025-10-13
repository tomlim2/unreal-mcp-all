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


// Transform request data (image-to-image)
export interface TransformRequest {
  prompt: string;
  main_prompt?: string;
  reference_prompts?: string[];
  model: string;
  sessionId: string;
  mainImageData?: {data: string; mime_type: string}; // User-uploaded main image
  referenceImageData?: Array<{data: string; mime_type: string}>;
}

// Text-to-image generation request data
export interface GenerateImageRequest {
  prompt: string;
  text_prompt: string;  // Main generation prompt
  aspect_ratio?: string;  // Default "16:9"
  model: string;
  sessionId: string;
  referenceImageData?: Array<{data: string; mime_type: string}>; // Style references only
  reference_prompts?: string[];
}

// Create session with image generation request
export interface CreateSessionWithImageRequest {
  prompt: string;
  main_prompt?: string;
  text_prompt?: string;
  aspect_ratio?: string;
  model: string;
  session_name?: string;
  mainImageData?: {data: string; mime_type: string};
  referenceImageData?: Array<{data: string; mime_type: string}>;
  reference_prompts?: string[];
}

// Create session with image generation response
export interface CreateSessionWithImageResponse {
  success: boolean;
  session_id: string;
  session_name: string;
  image_uid?: string;
  image_url?: string;
  redirect_url: string;
  error?: string;
  nlp_result?: unknown;
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

  // Image transformation with reference images
  transform: (data: TransformRequest) => Promise<AIResponse>;

  // Create session with image generation (for first page)
  createSessionWithImage: (data: CreateSessionWithImageRequest) => Promise<CreateSessionWithImageResponse>;

  // Context history
  getSessionContext: (sessionId: string) => Promise<SessionContext>;
}