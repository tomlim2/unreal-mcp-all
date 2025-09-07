"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Session } from "../services";
import SessionListItem from "./SessionListItem";
import styles from "./SessionSidebar.module.css";

interface SessionSidebarProps {
  sessionInfo: Session[];
  loading: boolean;
  activeSessionId: string | null;
  onSessionDelete: (sessionId: string) => Promise<void>;
}

export default function SessionSidebar({ 
  sessionInfo, 
  loading, 
  activeSessionId, 
  onSessionDelete,
}: SessionSidebarProps) {
  const router = useRouter();

  const handleNewSession = () => {
    router.push('/app');
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
      <div className={styles.header}>
        <h1 className={styles.title}>Mega Melange</h1>
      </div>
      <div className={styles.sessionControls}>
        <button
          onClick={handleNewSession}
          className={styles.newSessionButton}
        >
          New Session
        </button>
      </div>
      <div className={styles.recentSection}>
        <h2 className={styles.recentTitle}>Recent</h2>
      </div>
      <div className={styles.sessionList}>
        {!sessionInfo || sessionInfo.length === 0 ? (
          <div className={styles.noSessions}>No sessions found (total: {sessionInfo?.length || 0})</div>
        ) : (
          sessionInfo.map((session) => (
            <SessionListItem
              key={session.session_id}
              sessionId={session.session_id}
              sessionName={session.session_name || 'Untitled Session'}
              isActive={activeSessionId === session.session_id}
              onDelete={deleteSpecificSession}
            />
          ))
        )}
      </div>
    </div>
  );
}
