'use client';

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useSessionContext } from "../layout";
import styles from "../page.module.css";

export default function AppHome() {
  const router = useRouter();
  const { sessionInfo, sessionsLoaded } = useSessionContext();

  useEffect(() => {
    if (sessionsLoaded) {
      if (sessionInfo.length > 0) {
        // Redirect to first session
        router.replace(`/app/${sessionInfo[0].session_id}`);
      } else {
        // No sessions available, stay on /app and show empty state
        console.log('No sessions available');
      }
    }
  }, [sessionsLoaded, sessionInfo, router]);

  if (!sessionsLoaded) {
    return (
      <div className={styles.page}>
        <main className={styles.main}>
          <div style={{ 
            display: 'flex', 
            justifyContent: 'center', 
            alignItems: 'center', 
            height: '100vh',
            color: '#666666',
            fontSize: '0.95rem'
          }}>
            Loading sessions...
          </div>
        </main>
      </div>
    );
  }

  if (sessionInfo.length === 0) {
    return (
      <div className={styles.page}>
        <main className={styles.main}>
          <div style={{ 
            display: 'flex', 
            justifyContent: 'center', 
            alignItems: 'center', 
            height: '100vh',
            color: '#999999',
            fontSize: '0.95rem',
            fontStyle: 'italic'
          }}>
            No sessions available. Create a new session to get started.
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <main className={styles.main}>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center', 
          height: '100vh',
          color: '#666666',
          fontSize: '0.95rem'
        }}>
          Redirecting to first session...
        </div>
      </main>
    </div>
  );
}