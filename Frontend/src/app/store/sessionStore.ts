import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface SessionState {
  sessionId: string | null;
  setSessionId: (sessionId: string | 'all') => void;
  clearSession: () => void;
  generateNewSession: () => string;
  isAllSessions: () => boolean;
}

export const useSessionStore = create<SessionState>()(
  persist(
    (set, get) => ({
      sessionId: null,
      
      setSessionId: (sessionId: string | 'all') => {
        set({ sessionId });
      },
      
      clearSession: () => {
        set({ sessionId: null });
      },
      
      generateNewSession: () => {
        const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        set({ sessionId: newSessionId });
        return newSessionId;
      },
      
      isAllSessions: () => {
        const { sessionId } = get();
        return sessionId === 'all';
      },
    }),
    {
      name: 'unreal-session-storage',
      getStorage: () => localStorage,
    }
  )
);