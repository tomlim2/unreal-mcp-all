'use client';

import { useState, useEffect, createContext, useContext, ReactNode, useMemo } from "react";
import { useRouter, usePathname } from "next/navigation";
import { createApiService, Session } from "../services";
import { useSessionStore } from "../store/sessionStore";
import Sidebar from "../components/sidebar/Sidebar";
import styles from "../components/SessionManagerPanel.module.css";

// Session Context Types
interface SessionContextType {
  // Session data
  sessionInfo: Session[];
  sessionsLoaded: boolean;
  sessionsLoading: boolean;
  
  // Active session
  sessionId: string | null;
  setSessionId: (id: string | null) => void;
  
  // Session operations
  handleCreateSession: (name: string) => Promise<Session | null>;
  handleDeleteSession: (sid: string) => Promise<void>;
  handleRenameSession: (sid: string, name: string) => Promise<void>;
  handleSelectSession: (sid: string) => void;
  
  // Error handling
  error: string | null;
  setError: (error: string | null) => void;
}

// Create Session Context
const SessionContext = createContext<SessionContextType | null>(null);

// Custom hook to use session context
export const useSessionContext = () => {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error('useSessionContext must be used within a SessionProvider');
  }
  return context;
};

// Session Provider Component  
function SessionProvider({ children }: { children: ReactNode }) {
  const { sessionId, setSessionId } = useSessionStore();
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const pathname = usePathname();
  
  // Session management state
  const [sessionInfo, setSessionInfo] = useState<Session[]>([]);
  const [sessionsLoaded, setSessionsLoaded] = useState(false);
  const [sessionsLoading, setSessionsLoading] = useState(true);
  
  // Create apiService once and memoize it
  const apiService = useMemo(() => createApiService(), []);

  // Only load sessions once on mount
  useEffect(() => {
    let isMounted = true;
    
    const loadSessions = async () => {
      try {
        const sessions = await apiService.getSessions();
        if (isMounted) {
          setSessionInfo(sessions);
          if (sessions.length > 0 && !sessionId && pathname !== '/app') {
            setSessionId(sessions[0].session_id);
          }
          setSessionsLoaded(true);
        }
      } catch (error) {
        if (isMounted) {
          console.error('Failed to fetch sessions:', error);
          setError('Failed to load sessions');
        }
      } finally {
        if (isMounted) {
          setSessionsLoading(false);
        }
      }
    };

    loadSessions();
    
    return () => {
      isMounted = false;
    };
  }, []); // Only run once on mount

  const fetchSessions = async () => {
    try {
      const sessions = await apiService.getSessions();
      setSessionInfo(sessions);
      setSessionsLoaded(true);
    } catch (error) {
      console.error('Failed to fetch sessions:', error);
      setError('Failed to load sessions');
    }
  };

  const handleCreateSession = async (name: string): Promise<Session | null> => {
    try {
      const session = await apiService.createSession(name);
      setSessionId(session.session_id);
      await fetchSessions(); // Refresh the list
      return { 
        session_id: session.session_id, 
        session_name: session.session_name,
        created_at: new Date().toISOString(),
        last_accessed: new Date().toISOString()
      };
    } catch (error) {
      console.error('Failed to create session:', error);
      setError('Failed to create session');
      return null;
    }
  };

  const handleDeleteSession = async (sid: string) => {
    try {
      const isCurrentSession = sessionId === sid;
      
      await apiService.deleteSession(sid);
      await fetchSessions(); // Refresh the list
      
      if (isCurrentSession) {
        // If deleting current session, redirect to /app
        setSessionId(null);
        router.push('/app');
      } else {
        // If not current session, select first remaining session if available
        const remainingSessions = sessionInfo.filter(s => s.session_id !== sid);
        if (remainingSessions.length > 0) {
          setSessionId(remainingSessions[0].session_id);
        }
      }
    } catch (error) {
      console.error('Failed to delete session:', error);
      setError('Failed to delete session');
    }
  };

  const handleRenameSession = async (sid: string, name: string) => {
    try {
      await apiService.renameSession(sid, name);
      await fetchSessions(); // Refresh the list
    } catch (error) {
      console.error('Failed to rename session:', error);
      setError('Failed to rename session');
    }
  };

  const handleSelectSession = (sid: string) => {
    setSessionId(sid);
  };

  const contextValue: SessionContextType = {
    sessionInfo,
    sessionsLoaded,
    sessionsLoading,
    sessionId,
    setSessionId,
    handleCreateSession,
    handleDeleteSession,
    handleRenameSession,
    handleSelectSession,
    error,
    setError
  };

  // Determine active session ID based on current route
  const getActiveSessionId = () => {
    if (pathname === '/app') return null; // No active session on new session page
    if (pathname?.startsWith('/app/')) {
      const pathSessionId = pathname.split('/app/')[1];
      return pathSessionId || null;
    }
    return sessionId;
  };

  return (
    <SessionContext.Provider value={contextValue}>
      <div className={styles.container}>
        <Sidebar 
          sessionInfo={sessionInfo}
          activeSessionId={getActiveSessionId()}
          onSessionDelete={handleDeleteSession}
          loading={sessionsLoading}
        />
        <div className={styles.mainContent}>
          {children}
        </div>
      </div>
    </SessionContext.Provider>
  );
}

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <SessionProvider>
      {children}
    </SessionProvider>
  );
}