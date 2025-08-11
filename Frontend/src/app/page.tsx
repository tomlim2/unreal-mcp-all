import UnrealAIChat from "./components/UnrealAIChat";
import styles from "./page.module.css";

export default function Home() {
  return (
    <div className={styles.page}>
      <main className={styles.main}>
        <UnrealAIChat />
      </main>
    </div>
  );
}
