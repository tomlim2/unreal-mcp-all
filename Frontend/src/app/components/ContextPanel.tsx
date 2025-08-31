'use client';

import { useState } from "react";
import { useSessionStore } from "../store/sessionStore";
import { createApiService } from "../services";
import SessionController from "./SessionController";
import ContextHistory from "./ContextHistory";
import UnrealAIChat from "./UnrealAIChat";
import styles from "./ContextPanel.module.css";

export default function ContextPanel() {
  const { sessionId, setSessionId } = useSessionStore();
  const [error, setError] = useState<string | null>(null);

  // Create API service with dependencies
  const apiService = createApiService(sessionId, setSessionId, setError);

  return (
    <div className={styles.contextPanel}>
      {error && (
        <div className={styles.globalError}>
          <span>⚠️ {error}</span>
          <button onClick={() => setError(null)}>×</button>
        </div>
      )}
      <SessionController apiService={apiService} />
      <ContextHistory apiService={apiService} />
      <UnrealAIChat apiService={apiService} />
    </div>
  );
}
