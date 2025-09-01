"use client";

import { useState, useEffect } from "react";
import { useSessionStore } from "../store/sessionStore";
import { ApiService, Session } from "../services";
import SessionItem from "./SessionItem";
import styles from "./SessionController.module.css";

interface SessionControllerProps {
  apiService: ApiService;
  onSessionsLoaded?: (loaded: boolean) => void;
}

export default function SessionController({ apiService, onSessionsLoaded }: SessionControllerProps) {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sessionName, setSessionName] = useState("");
  const [creating, setCreating] = useState(false);
  const [deletingSessionId, setDeletingSessionId] = useState<string | null>(null);
  const { sessionId, setSessionId } = useSessionStore();

  useEffect(() => {
    fetchSessions(true); // Initial load with loading state
  }, []);

  const fetchSessions = async (isInitialLoad = false) => {
    try {
      // Only show loading state on initial load to prevent blinking
      if (isInitialLoad) {
        setLoading(true);
      }
      setError(null);

      const sessions = await apiService.fetchSessions();
      setSessions(sessions);
      console.log('SessionController loaded sessions:', sessions.length);
      
      // Notify parent that sessions are loaded
      if (onSessionsLoaded) {
        onSessionsLoaded(true);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch sessions");
      if (onSessionsLoaded) {
        onSessionsLoaded(false);
      }
    } finally {
      if (isInitialLoad) {
        setLoading(false);
      }
    }
  };

  const addSessions = async () => {
    if (!sessionName.trim()) {
      setError("Please enter a session name");
      return;
    }

    if (sessionName.length > 50) {
      setError("Session name must be 50 characters or less");
      return;
    }

    setCreating(true);
    setError(null);

    try {
      const result = await apiService.createSession(sessionName);

      // Clear input and refresh sessions without loading state
      setSessionName("");
      await fetchSessions(false); // No loading state to prevent blinking

      // Set the newly created session as active using server-generated ID
      if (result.session_id) {
        setSessionId(result.session_id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create session");
    } finally {
      setCreating(false);
    }
  };

  const deleteSpecificSession = async (sessionIdToDelete: string) => {
    // Ask for confirmation
    const sessionToDelete = sessions.find(s => s.session_id === sessionIdToDelete);
    const sessionDisplayName = sessionToDelete?.session_name || `Session ${sessionIdToDelete.slice(0, 8)}`;
    
    if (!window.confirm(`Are you sure you want to delete "${sessionDisplayName}" and all its conversation history? This action cannot be undone.`)) {
      return;
    }

    setDeletingSessionId(sessionIdToDelete);
    setError(null);

    try {
      await apiService.deleteSession(sessionIdToDelete);

      // If the deleted session was currently selected, clear selection
      if (sessionId === sessionIdToDelete) {
        setSessionId(null);
      }
      
      await fetchSessions(false); // No loading state to prevent blinking
      
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete session");
    } finally {
      setDeletingSessionId(null);
    }
  };

  const handleSessionSelect = (selectedSessionId: string) => {
    setSessionId(selectedSessionId);
  };


  if (loading) {
    return (
      <div className={styles.container}>
        <div className={styles.loading}>Loading sessions...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.container}>
        <div className={styles.error}>
          Error: {error}
          <button onClick={() => fetchSessions(false)} className={styles.retryButton}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.sessionControls}>
        <button onClick={() => fetchSessions(false)} className={styles.refreshButton}>
          Refresh Sessions
        </button>

        <div className={styles.addSessionForm}>
          <textarea
            value={sessionName}
            onChange={(e) => setSessionName(e.target.value)}
            placeholder="Enter session name (e.g., 'Morning Build', 'Testing Scene')"
            className={styles.sessionNameInput}
            maxLength={50}
            rows={2}
            disabled={creating}
          />
          <button
            onClick={addSessions}
            className={`${styles.refreshButton} ${
              creating ? styles.loading : ""
            }`}
            disabled={creating || !sessionName.trim()}
          >
            {creating ? "Creating..." : "Add Session"}
          </button>
          {sessionName.length > 40 && (
            <div className={styles.charCount}>
              {sessionName.length}/50 characters
            </div>
          )}
        </div>
      </div>
      <div className={styles.sessionList}>
        {sessions.length === 0 ? (
          <div className={styles.noSessions}>No sessions found (total: {sessions.length})</div>
        ) : (
          sessions.map((session) => (
            <SessionItem
              key={session.session_id}
              session={session}
              isActive={sessionId === session.session_id}
              onSelect={() => handleSessionSelect(session.session_id)}
              onDelete={deleteSpecificSession}
              isDeleting={deletingSessionId === session.session_id}
            />
          ))
        )}
      </div>
    </div>
  );
}
