"use client";

import { useRouter } from "next/navigation";
import { Session } from "../services";
import styles from "./SessionListItem.module.css";

interface SessionListItemProps {
  sessionId: string;
  sessionName: string;
  isActive: boolean;
  onDelete?: (sessionId: string) => void;
  isDeleting?: boolean;
}

export default function SessionListItem({
  sessionId,
  sessionName,
  isActive,
  onDelete,
  isDeleting = false,
}: SessionListItemProps) {
  const router = useRouter();

  const handleSelect = () => {
    router.push(`/app/${sessionId}`);
  };

  return (
    <div
      className={`${styles.sessionItem} ${isActive ? styles.active : ""}`}
      onClick={handleSelect}
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