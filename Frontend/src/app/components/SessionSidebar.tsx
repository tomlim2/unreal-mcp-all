"use client";

import { useState } from "react";
import { Session } from "../services";
import SessionListItem from "./SessionListItem";
import styles from "./SessionSidebar.module.css";

interface SessionSidebarProps {
  sessionInfo: Session[];
  loading: boolean;
  error: string | null;
  activeSessionId: string | null;
  onSessionCreate: (sessionName: string) => Promise<Session | null>;
  onSessionDelete: (sessionId: string) => Promise<void>;
  onSessionRename: (sessionId: string, name: string) => Promise<void>;
}

export default function SessionSidebar({ 
  sessionInfo, 
  loading, 
  error, 
  activeSessionId, 
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
              onDelete={deleteSpecificSession}
              isDeleting={deletingSessionId === session.session_id}
            />
          ))
        )}
      </div>
    </div>
  );
}
