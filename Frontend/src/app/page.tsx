import UnrealLlmChat from "./components/UnrealAIChat";
import SessionController from "./components/SessionController";
import ContextPanel from "./components/ContextPanel";
import styles from "./page.module.css";

export default function Home() {
  return (
    <div className={styles.page}>
      <main className={styles.main}>
        <ContextPanel />
        <UnrealLlmChat />
      </main>
    </div>
  );
}
