import SessionController from "./SessionController";
import ContextHistory from "./ContextHistory";
import styles from "./ContextPanel.module.css";

export default function ContextPanel() {
  return (
    <div className={styles.contextPanel}>
      <SessionController />
      <ContextHistory />
    </div>
  );
}
