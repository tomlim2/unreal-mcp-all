import SessionManagerPanel from "./components/SessionManagerPanel";
import styles from "./page.module.css";

export default function Home() {
  return (
    <div className={styles.page}>
      <main className={styles.main}>
        <SessionManagerPanel />
      </main>
    </div>
  );
}
