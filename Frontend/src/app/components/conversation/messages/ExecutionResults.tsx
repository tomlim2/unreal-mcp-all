'use client';

import styles from './MessageItem.module.css';
import MessageItemImageResult from './MessageItemImageResult';

interface ExecutionResultData {
  command: string;
  success: boolean;
  result?: unknown;
  error?: string;
}

interface ExecutionResultsProps {
  executionResults?: ExecutionResultData[];
  excludeImages?: boolean;
}

export default function ExecutionResults({ executionResults, excludeImages = false }: ExecutionResultsProps) {
  if (!executionResults || executionResults.length === 0) {
    return null;
  }

  // Filter results based on excludeImages prop
  const filteredResults = excludeImages 
    ? executionResults.filter(result => !(
        result.result && 
        typeof result.result === 'object' && 
        result.result !== null &&
        'image_url' in result.result
      ))
    : executionResults;

  if (filteredResults.length === 0) {
    return null;
  }

  return (
    <div className={styles.results}>
      <strong>Unreal Engine Execution Results:</strong>
      {filteredResults.map((result, resultIndex) => (
        <div key={resultIndex} className={`${styles.result} ${result.success ? styles.success : styles.failure}`}>
          <div className={styles.resultHeader}>
            <div className={`${styles.statusCircle} ${result.success ? styles.successCircle : styles.failureCircle}`}></div>
            <span className={styles.commandName}>{result.command}</span>
          </div>
          <MessageItemImageResult result={result} resultIndex={resultIndex} />
        </div>
      ))}
    </div>
  );
}