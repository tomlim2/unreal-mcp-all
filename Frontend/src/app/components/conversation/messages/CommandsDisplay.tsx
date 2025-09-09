'use client';

import styles from './MessageItem.module.css';

interface Command {
  type: string;
  params: Record<string, unknown>;
}

interface CommandsDisplayProps {
  commands?: Command[];
}

export default function CommandsDisplay({ commands }: CommandsDisplayProps) {
  if (!commands || commands.length === 0) {
    return null;
  }

  return (
    <div className={styles.commands}>
      <strong>AI Generated Commands:</strong>
      {commands.map((cmd, cmdIndex) => (
        <pre key={cmdIndex} className={styles.command}>
          <div className={styles.commandHeader}>
            <strong>{cmd.type}</strong>
            <span className={styles.languageLabel}>json</span>
          </div>
          <div className={styles.commandContent}>
            {JSON.stringify(cmd.params, null, 2)}
          </div>
        </pre>
      ))}
    </div>
  );
}