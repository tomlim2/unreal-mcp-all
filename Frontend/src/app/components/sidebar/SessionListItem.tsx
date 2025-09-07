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
    router.push(`/app/${sessionId}`, { scroll: false });
  };

  return (
    <div className={`${styles.sessionItemContainer} ${isActive ? styles.active : ""}`}>
      <button
        className={`${styles.sessionItem} ${isActive ? styles.active : ""}`}
        onClick={handleSelect}
      >
        {sessionName || `Session ${sessionId.slice(0, 8)}`}
      </button>
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
  );
}