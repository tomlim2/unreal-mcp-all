"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Session } from "../../services";
import SessionListItem from "./SessionListItem";
import useModal from "../modal/useModal";
import styles from "./Sidebar.module.css";

interface SidebarProps {
  sessionInfo: Session[];
  activeSessionId: string | null;
  onSessionDelete: (sessionId: string) => Promise<void>;
  loading?: boolean;
}

export default function Sidebar({ 
  sessionInfo, 
  activeSessionId, 
  onSessionDelete,
  loading = false,
}: SidebarProps) {
  const router = useRouter();
  const { showConfirm } = useModal();

  const handleNewSession = () => {
    router.push('/app');
  };

  const deleteSpecificSession = async (sessionIdToDelete: string) => {
    const sessionToDelete = sessionInfo.find(s => s.session_id === sessionIdToDelete);
    const sessionName = sessionToDelete?.session_name || 'Untitled Session';
    
    const confirmed = await showConfirm({
      title: 'Delete Session',
      message: `Are you sure you want to delete "${sessionName}"? This action cannot be undone.`,
      variant: 'danger',
      confirmText: 'Delete',
      cancelText: 'Cancel'
    });
    
    if (confirmed) {
      onSessionDelete(sessionIdToDelete);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>Mega Melange</h1>
        <p className={styles.description}>
			Natural language control for Unreal Engine workflows
        </p>
      </div>
      <div className={styles.sessionControls}>
        <button
          onClick={handleNewSession}
          className={styles.newSessionButton}
          disabled={loading}
        >
          New Session
        </button>
      </div>
      <div className={styles.recentSection}>
        <h2 className={styles.recentTitle}>Recent</h2>
      </div>
      <div className={styles.sessionList}>
        {!sessionInfo || sessionInfo.length === 0 ? (
          <div className={styles.noSessions}></div>
        ) : (
          sessionInfo.map((session) => (
            <SessionListItem
              key={session.session_id}
              sessionId={session.session_id}
              sessionName={session.session_name || 'Untitled Session'}
              isActive={activeSessionId === session.session_id}
              onDelete={deleteSpecificSession}
              loading={loading}
            />
          ))
        )}
      </div>
      <div className={styles.footer}>
        <h3 className={styles.todoTitle}>Next Steps</h3>
        <ul className={styles.todoList}>
          <li className={styles.todoItem}>Add Nano banana</li>
          <li className={styles.todoItem}>Add get actors by activated viewport</li>
          <li className={styles.todoItem}>And more function</li>
        </ul>
        <p className={styles.copyright}>
          github repo available soon
        </p>
      </div>
    </div>
  );
}
