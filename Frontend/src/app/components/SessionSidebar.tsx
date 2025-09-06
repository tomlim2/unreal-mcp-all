"use client";

import { useState } from "react";
import SessionListItem from "./SessionListItem";
import styles from "./SessionSidebar.module.css";

interface SessionSidebarProps {
  sessionInfo: any[];
  loading: boolean;
  error: string | null;
  activeSessionId: string | null;
  onSessionSelect: (sessionId: string) => void;
  onSessionCreate: (sessionName: string) => Promise<{ session_id?: string }>;
  onSessionDelete: (sessionId: string) => Promise<void>;
  onSessionRename: (sessionId: string, name: string) => Promise<void>;
}

export default function SessionSidebar({ 
  sessionInfo, 
  loading, 
  error, 
  activeSessionId, 
  onSessionSelect, 
  onSessionCreate, 
  onSessionDelete,
  onSessionRename,
}: SessionSidebarProps) {
  const [sessionName, setSessionName] = useState("");
  const [creating, setCreating] = useState(false);
  const [deletingSessionId, setDeletingSessionId] = useState<string | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);

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

  const deleteSpecificSession = (sessionIdToDelete: string) => {
    onSessionDelete(sessionIdToDelete);

    // Ask for confirmation
    // const sessionToDelete = sessionInfo.find(s => s.session_id === sessionIdToDelete);
    // const sessionDisplayName = sessionToDelete?.session_name || `Session ${sessionIdToDelete.slice(0, 8)}`;
    
    // if (!window.confirm(`Are you sure you want to delete "${sessionDisplayName}" and all its conversation history? This action cannot be undone.`)) {
    //   return;
    // }

    // setDeletingSessionId(sessionIdToDelete);
    // setLocalError(null);

    // try {
    // } catch (err) {
    //   setLocalError(err instanceof Error ? err.message : "Failed to delete session");
    // } finally {
    //   setDeletingSessionId(null);
    // }
  };


  if (loading) {
    return (
      <div className={styles.container}>
        <div className={styles.loading}>Loading sessions...</div>
      </div>
    );
  }


  return (
    <div className={styles.container}>
      <div className={styles.sessionControls}>
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
        {!sessionInfo || sessionInfo.length === 0 ? (
          <div className={styles.noSessions}>No sessions found (total: {sessionInfo?.length || 0})</div>
        ) : (
          sessionInfo.map((session) => (
            <SessionListItem
              key={session.session_id}
              sessionId={session.session_id}
              sessionName={session.session_name}
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
