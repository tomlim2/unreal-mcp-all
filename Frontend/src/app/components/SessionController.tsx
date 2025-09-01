"use client";

import { useState } from "react";
import { Session } from "../services";
import SessionItem from "./SessionItem";
import styles from "./SessionController.module.css";

interface SessionControllerProps {
  sessions: Session[];
  loading: boolean;
  error: string | null;
  activeSessionId: string | null;
  onSessionSelect: (sessionId: string) => void;
  onSessionCreate: (sessionName: string) => Promise<{ session_id?: string }>;
  onSessionDelete: (sessionId: string) => Promise<void>;
  onRefresh: () => void;
}

export default function SessionController({ 
  sessions, 
  loading, 
  error, 
  activeSessionId, 
  onSessionSelect, 
  onSessionCreate, 
  onSessionDelete, 
  onRefresh 
}: SessionControllerProps) {
  const [sessionName, setSessionName] = useState("");
  const [creating, setCreating] = useState(false);
  const [deletingSessionId, setDeletingSessionId] = useState<string | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);

  // Display error from parent or local error
  const displayError = error || localError;

  const addSessions = async () => {
    if (!sessionName.trim()) {
      setLocalError("Please enter a session name");
      return;
    }

    if (sessionName.length > 50) {
      setLocalError("Session name must be 50 characters or less");
      return;
    }

    setCreating(true);
    setLocalError(null);

    try {
      await onSessionCreate(sessionName);
      setSessionName("");
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Failed to create session");
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
    setLocalError(null);

    try {
      await onSessionDelete(sessionIdToDelete);
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Failed to delete session");
    } finally {
      setDeletingSessionId(null);
    }
  };


  if (loading) {
    return (
      <div className={styles.container}>
        <div className={styles.loading}>Loading sessions...</div>
      </div>
    );
  }

  if (displayError) {
    return (
      <div className={styles.container}>
        <div className={styles.error}>
          Error: {displayError}
          <button onClick={() => {
            setLocalError(null);
            onRefresh();
          }} className={styles.retryButton}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.sessionControls}>
        <button onClick={onRefresh} className={styles.refreshButton}>
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
              isActive={activeSessionId === session.session_id}
              onSelect={() => onSessionSelect(session.session_id)}
              onDelete={deleteSpecificSession}
              isDeleting={deletingSessionId === session.session_id}
            />
          ))
        )}
      </div>
    </div>
  );
}
