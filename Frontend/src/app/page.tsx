'use client';

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import styles from "./page.module.css";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    // Simple redirect to /app
    router.replace('/app');
  }, [router]);

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
          Redirecting to app...
        </div>
      </main>
    </div>
  );
}
