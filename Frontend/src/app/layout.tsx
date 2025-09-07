'use client';

import { Inter, Bodoni_Moda } from "next/font/google";
import { useState, useEffect, createContext, useContext, ReactNode, useCallback, useMemo } from "react";
import { createApiService, Session } from "./services";
import { useSessionStore } from "./store/sessionStore";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const bodoniModa = Bodoni_Moda({
  variable: "--font-bodoni-moda",
  subsets: ["latin"],
  weight: ["400", "700"],
});

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
          if (sessions.length > 0 && !sessionId) {
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
      await apiService.deleteSession(sid);
      if (sessionId === sid) {
        setSessionId(null);
      }
      await fetchSessions(); // Refresh the list
      // Select first remaining session if available
      const remainingSessions = sessionInfo.filter(s => s.session_id !== sid);
      if (remainingSessions.length > 0) {
        setSessionId(remainingSessions[0].session_id);
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

  return (
    <SessionContext.Provider value={contextValue}>
      {children}
    </SessionContext.Provider>
  );
}

export default function RootLayout({
  children,
  params,
}: Readonly<{
  children: React.ReactNode;
  params?: Promise<any>;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.variable} ${bodoniModa.variable}`} suppressHydrationWarning>
        <SessionProvider>
          {children}
        </SessionProvider>
      </body>
    </html>
  );
}
