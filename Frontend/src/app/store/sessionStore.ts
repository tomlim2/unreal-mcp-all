import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface SessionState {
  sessionId: string | null;
  setSessionId: (sessionId: string | 'all') => void;
  clearSession: () => void;
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