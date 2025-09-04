'use client';

import { useState, useEffect } from 'react';
import styles from './MessageItem.module.css';

interface ChatMessage {
  timestamp: string;
  role: 'user' | 'assistant' | 'system' | 'job';
  content: string;
  commands?: Array<{
    type: string;
    params: Record<string, unknown>;
  }>;
  execution_results?: Array<{
    command: string;
    success: boolean;
    result?: unknown;
    error?: string;
  }>;
  job_status?: 'pending' | 'running' | 'completed' | 'failed';
  job_progress?: number; // 0-100
  image_url?: string;
}

interface MessageItemProps {
  message: ChatMessage;
  sessionName?: string;
  index: number;
  sessionId?: string;
  previousMessage?: ChatMessage;
}

export default function MessageItem({ message, sessionName, index, sessionId, previousMessage }: MessageItemProps) {
  const keyPrefix = sessionId ? `${sessionId}-${index}` : index;
  const [isExpanded, setIsExpanded] = useState(false);

  // Reset expanded state when sessionId changes
  useEffect(() => {
    setIsExpanded(false);
  }, [sessionId]);

  // User message rendering
  if (message.role === 'user') {
    return (
      <div key={keyPrefix} className={`${styles.message} ${styles.user}`}>
        <div className={styles.messageHeader}>
          <span className={styles.roleLabel}>User</span>
          {sessionName && (
            <span className={styles.sessionName}>{sessionName}</span>
          )}
        </div>
        <div className={styles.messageContent}>
          {message.content}
        </div>
      </div>
    );
  }

  // Assistant message rendering
  if (message.role === 'assistant') {
    // Determine success/failure status for assistant messages
    const getAssistantStatus = () => {
      if (!message.execution_results || message.execution_results.length === 0) {
        return { status: 'neutral', text: 'Response' };
      }
      
      const hasFailures = message.execution_results.some(result => !result.success);
      return hasFailures 
        ? { status: 'failure', text: 'Error' }
        : { status: 'success', text: 'Success' };
    };

    const { status, text } = getAssistantStatus();

    return (
      <div 
        key={keyPrefix} 
        className={`${styles.message} ${styles.assistant}`}
        style={{
          borderLeft: `12px solid ${
            status === 'success' ? '#22c55e' : 
            status === 'failure' ? '#ef4444' : 
            '#6b7280'
          }`
        }}
      >
        <div 
          className={`${styles.messageHeader} ${styles.clickable}`}
          onClick={() => setIsExpanded(!isExpanded)}
          title={isExpanded ? "Click to collapse" : "Click to expand"}
          style={{
            cursor: 'pointer'
          }}
        >
          <div className={styles.headerLeft}>
            <span className={styles.roleLabel}>Assistant</span>
          </div>
          <div className={styles.headerRight}>
            {sessionName && (
              <span className={styles.sessionName}>{sessionName}</span>
            )}
            <span className={`${styles.expandIcon} ${isExpanded ? styles.expanded : ''}`}>
              {isExpanded ? '-' : '+'}
            </span>
          </div>
        </div>
        
        {isExpanded && (
          <>
            <div className={styles.messageContent}>
              {message.content}
            </div>
            
            {message.commands && message.commands.length > 0 && (
              <div className={styles.commands}>
                <strong>Commands:</strong>
                {message.commands.map((cmd, cmdIndex) => (
                  <div key={cmdIndex} className={styles.command}>
                    <code>{cmd.type}</code>
                    <pre>{JSON.stringify(cmd.params, null, 2)}</pre>
                  </div>
                ))}
              </div>
            )}
            
            {message.execution_results && message.execution_results.length > 0 && (
              <div className={styles.results}>
                <strong>Results:</strong>
                {message.execution_results.map((result, resultIndex) => (
                  <div key={resultIndex} className={`${styles.result} ${result.success ? styles.success : styles.failure}`}>
                    <div className={styles.resultHeader}>
                      {result.command} - {result.success ? '✅ Success' : '❌ Failed'}
                    </div>
                    {result.success ? (
                      <div>
                        <pre className={styles.resultData}>
                          {JSON.stringify(result.result, null, 2)}
                        </pre>
                        {/* Display screenshot if available */}
                        {result.result && typeof result.result === 'object' && 'image_url' in result.result && (
                          <div className={styles.screenshotContainer}>
                            <img 
                              src={result.result.image_url as string} 
                              alt="Screenshot" 
                              className={styles.screenshot}
                              onError={(e) => {
                                console.error('Failed to load screenshot:', result.result.image_url);
                                e.currentTarget.style.display = 'none';
                              }}
                            />
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className={styles.errorMessage}>{result.error}</div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    );
  }

  // System message rendering
  if (message.role === 'system') {
    return (
      <div key={keyPrefix} className={`${styles.message} ${styles.system}`}>
        <div className={styles.messageHeader}>
          <span className={styles.roleLabel}>System</span>
          {sessionName && (
            <span className={styles.sessionName}>{sessionName}</span>
          )}
        </div>
        <div className={styles.messageContent}>
          {message.content}
        </div>
      </div>
    );
  }

  // Job Status message rendering
  if (message.role === 'job') {
    const getJobStatusColor = () => {
      switch (message.job_status) {
        case 'completed': return '#22c55e'; // Green
        case 'failed': return '#ef4444'; // Red
        case 'running': return '#3b82f6'; // Blue
        case 'pending': return '#f59e0b'; // Orange
        default: return '#6b7280'; // Gray
      }
    };

    const getJobStatusText = () => {
      switch (message.job_status) {
        case 'completed': return 'Completed';
        case 'failed': return 'Failed';
        case 'running': return 'Running';
        case 'pending': return 'Pending';
        default: return 'Job';
      }
    };

    return (
      <div 
        key={keyPrefix} 
        className={`${styles.message} ${styles.job}`}
        style={{
          borderLeft: `12px solid ${getJobStatusColor()}`
        }}
      >
        <div 
          className={`${styles.messageHeader} ${styles.clickable}`}
          onClick={() => setIsExpanded(!isExpanded)}
          title={isExpanded ? "Click to collapse" : "Click to expand"}
          style={{
            cursor: 'pointer'
          }}
        >
          <div className={styles.headerLeft}>
            <span className={styles.roleLabel}>Job Status</span>
            <span className={styles.jobStatus}>{getJobStatusText()}</span>
            {message.job_progress !== undefined && (
              <span className={styles.jobProgress}>({message.job_progress}%)</span>
            )}
          </div>
          <div className={styles.headerRight}>
            {sessionName && (
              <span className={styles.sessionName}>{sessionName}</span>
            )}
            <span className={`${styles.expandIcon} ${isExpanded ? styles.expanded : ''}`}>
              {isExpanded ? '-' : '+'}
            </span>
          </div>
        </div>
        
        {isExpanded && (
          <>
            <div className={styles.messageContent}>
              {message.content}
            </div>
            
            {message.image_url && (
              <div className={styles.jobImageContainer}>
                <img 
                  src={message.image_url} 
                  alt="Job Result" 
                  className={styles.jobImage}
                  onError={(e) => {
                    console.error('Failed to load job image:', message.image_url);
                    e.currentTarget.style.display = 'none';
                  }}
                />
              </div>
            )}
            
            {message.job_progress !== undefined && (
              <div className={styles.progressBar}>
                <div 
                  className={styles.progressFill}
                  style={{
                    width: `${message.job_progress}%`,
                    backgroundColor: getJobStatusColor()
                  }}
                />
              </div>
            )}
          </>
        )}
      </div>
    );
  }

  return null;
}