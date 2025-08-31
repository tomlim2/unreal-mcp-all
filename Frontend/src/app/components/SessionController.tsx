"use client";

import { useState, useEffect } from "react";
import { useSessionStore } from "../store/sessionStore";
import { ApiService, Session } from "../services";
import styles from "./SessionController.module.css";

interface SessionControllerProps {
  apiService: ApiService;
}

export default function SessionController({ apiService }: SessionControllerProps) {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sessionName, setSessionName] = useState("");
  const [creating, setCreating] = useState(false);
  const [deletingSessionId, setDeletingSessionId] = useState<string | null>(null);
  const { sessionId, setSessionId } = useSessionStore();

  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    try {
      setLoading(true);
      setError(null);

      const sessions = await apiService.fetchSessions();
      setSessions(sessions);
      console.log('SessionController loaded sessions:', sessions.length);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch sessions");
    } finally {
      setLoading(false);
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

      // Clear input and refresh sessions
      setSessionName("");
      await fetchSessions();

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

      // If the deleted session was currently selected, switch to "All Sessions"
      if (sessionId === sessionIdToDelete) {
        setSessionId('all');
      }
      
      await fetchSessions();
      
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete session");
    } finally {
      setDeletingSessionId(null);
    }
  };

  const handleSessionSelect = (selectedSessionId: string | "all") => {
    setSessionId(selectedSessionId);
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return dateString;
    }
  };

  if (loading) {
    return (
      <div className={styles.container}>
        <h2>Session Selector</h2>
        <div className={styles.loading}>Loading sessions...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.container}>
        <h2>Session Selector</h2>
        <div className={styles.error}>
          Error: {error}
          <button onClick={fetchSessions} className={styles.retryButton}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <h2>Session Selector</h2>
      <div className={styles.sessionControls}>
        <button onClick={fetchSessions} className={styles.refreshButton}>
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
        {/* All Sessions option */}
        <div
          className={`${styles.sessionItem} ${
            sessionId === "all" ? styles.active : ""
          }`}
          onClick={() => handleSessionSelect("all")}
        >
          <div className={styles.sessionId}>All Sessions</div>
          <div className={styles.sessionMeta}>
            <span>View all chat sessions</span>
            {sessions.length > 0 && (
              <span>{sessions.length} total sessions</span>
            )}
          </div>
        </div>

        {/* Individual sessions */}
        {sessions.length === 0 ? (
          <div className={styles.noSessions}>No sessions found (total: {sessions.length})</div>
        ) : (
          sessions.map((session) => (
            <div
              key={session.session_id}
              className={`${styles.sessionItem} ${
                sessionId === session.session_id ? styles.active : ""
              }`}
              onClick={() => handleSessionSelect(session.session_id)}
            >
              <div className={styles.sessionItemHeader}>
                <div className={styles.sessionId}>
                  {session.session_name ||
                    `Session ${session.session_id.slice(0, 8)}`}
                </div>
                <button
                  className={styles.sessionItemDelete}
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteSpecificSession(session.session_id);
                  }}
                  disabled={deletingSessionId !== null}
                  title="Delete session"
                >
                  {deletingSessionId === session.session_id ? '×' : '×'}
                </button>
              </div>
              <div className={styles.sessionItemContent}>
                <div className={styles.sessionMeta}>
                  <span>Created: {formatDate(session.created_at)}</span>
                  {session.interaction_count && (
                    <span>{session.interaction_count} interactions</span>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
      
    </div>
  );
}
