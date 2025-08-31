import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

interface SessionState {
  sessionId: string | null;
  setSessionId: (sessionId: string | null) => void;
  clearSession: () => void;
}

export const useSessionStore = create<SessionState>()(
  persist(
    (set) => ({
      sessionId: null,
      
      setSessionId: (sessionId: string | null) => {
        set({ sessionId });
      },
      
      clearSession: () => {
        set({ sessionId: null });
      },
    }),
    {
      name: 'unreal-session-storage',
      storage: createJSONStorage(() => localStorage),
    }
  )
);