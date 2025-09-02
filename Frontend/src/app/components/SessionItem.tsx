"use client";

import { Session } from "../services";
import styles from "./SessionItem.module.css";

interface SessionItemProps {
  sessionId: string;
  sessionName: string;
  isActive: boolean;
  onSelect: () => void;
  onDelete?: (sessionId: string) => void;
  isDeleting?: boolean;
}

export default function SessionItem({
  sessionId,
  sessionName,
  isActive,
  onSelect,
  onDelete,
  isDeleting = false,
}: SessionItemProps) {
  return (
    <div
      className={`${styles.sessionItem} ${isActive ? styles.active : ""}`}
      onClick={onSelect}
    >
      <div className={styles.sessionItemHeader}>
        <div className={styles.sessionId}>
          {sessionName ||
            `Session ${sessionName.slice(0, 8)}`}
        </div>
        {onDelete && (
          <button
            className={styles.sessionItemDelete}
            onClick={(e) => {
              e.stopPropagation();
              onDelete(sessionId);
            }}
            disabled={isDeleting}
            title="Delete session"
          >
            ×
          </button>
        )}
      </div>
      <div className={styles.sessionItemContent}>
        <div className={styles.sessionMeta}>
          {/* <span>Created: {formatDate(session.created_at)}</span>
          {session.interaction_count && (
            <span>{session.interaction_count} interactions</span>
          )} */}
        </div>
      </div>
    </div>
  );
}