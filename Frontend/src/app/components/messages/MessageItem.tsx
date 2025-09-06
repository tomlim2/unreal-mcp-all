'use client';

import { useState, useEffect } from 'react';
import styles from './MessageItem.module.css';
import MessageItemImageResult from './MessageItemImageResult';

function getFullImageUrl(imageUrl: string): string {
  // If it's already an absolute URL, return as-is
  if (imageUrl.startsWith('http://') || imageUrl.startsWith('https://')) {
    return imageUrl;
  }
  
  // If it's a relative URL starting with /api/screenshot/, make it absolute
  if (imageUrl.startsWith('/api/screenshot/')) {
    const httpBridgePort = process.env.NEXT_PUBLIC_HTTP_BRIDGE_PORT || '8080';
    return `http://localhost:${httpBridgePort}${imageUrl}`;
  }
  
  // Otherwise return as-is
  return imageUrl;
}

// Component to handle image loading with proper preloading
function ImageWithFallback({ 
  src, 
  alt, 
  className 
}: { 
  src: string; 
  alt: string; 
  className?: string; 
}) {
  const [imageSrc, setImageSrc] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    let mounted = true;
    
    console.log('Starting preload for:', src);
    
    // Preload the image before setting it as src
    const img = new Image();
    
    img.onload = () => {
      if (mounted) {
        console.log('Successfully preloaded job image:', src);
        console.log('Setting imageSrc and isLoading=false');
        setImageSrc(src);
        setIsLoading(false);
        setHasError(false);
      }
    };
    
    img.onerror = () => {
      if (mounted) {
        console.log('Failed to preload, retrying in 1 second...');
        // Retry after a delay
        setTimeout(() => {
          if (mounted) {
            img.src = src + '?retry=' + Date.now();
          }
        }, 1000);
      }
    };
    
    // Start loading
    img.src = src;
    
    return () => {
      mounted = false;
    };
  }, [src]);

  console.log('Render state:', { isLoading, hasError, imageSrc });

  if (isLoading) {
    console.log('Rendering loading state');
    return (
      <div className={className} style={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center', 
        minHeight: '100px',
        backgroundColor: '#333',
        color: '#ccc',
        fontSize: '12px'
      }}>
        Loading image...
      </div>
    );
  }

  if (hasError || !imageSrc) {
    console.log('Rendering error state');
    return (
      <div className={className} style={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center', 
        minHeight: '100px',
        backgroundColor: '#333',
        color: '#f44336',
        fontSize: '12px'
      }}>
        Failed to load image
      </div>
    );
  }

  console.log('Rendering image with src:', imageSrc);
  return (
    <img 
      src={imageSrc}
      alt={alt}
      className={className}
      onLoad={() => {
        console.log('Image displayed successfully:', imageSrc);
      }}
    />
  );
}

interface ExecutionResultData {
  command: string;
  success: boolean;
  result?: Record<string, any> & {
    image_url?: string;
  };
  error?: string;
}

interface ChatMessage {
  timestamp: string;
  role: 'user' | 'assistant' | 'system' | 'job';
  content: string;
  commands?: Array<{
    type: string;
    params: Record<string, unknown>;
  }>;
  execution_results?: ExecutionResultData[];
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
  
  // Set default expansion based on message role
  const getDefaultExpanded = () => {
    if (message.role === 'job') return true;     // Job messages always open
    if (message.role === 'assistant') return false; // Assistant messages closed by default
    return true; // Other messages open
  };
  
  const [isExpanded, setIsExpanded] = useState(getDefaultExpanded());

  // Reset expanded state when sessionId changes
  useEffect(() => {
    setIsExpanded(getDefaultExpanded());
  }, [sessionId]);

  // User message rendering
  if (message.role === 'user') {
    return (
      <div key={keyPrefix} className={`${styles.message} ${styles.user}`}>
        <div className={styles.messageHeader}>
          {sessionName && (
            <span className={styles.sessionName}>{sessionName}</span>
          )}
        </div>
        <div className={`${styles.messageContent} ${styles.resultContent}`}>
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

    // Extract image results to show always (not collapsed)
    const imageResults = message.execution_results?.filter(result => 
      result.success && result.result?.image_url
    ) || [];

    // Create preview of message content for header
    const getMessagePreview = (content: string, maxLength: number = 60) => {
      if (!content) return 'Assistant';
      
      // Remove extra whitespace and newlines
      const cleanContent = content.trim().replace(/\s+/g, ' ');
      
      if (cleanContent.length <= maxLength) {
        return cleanContent;
      }
      
      // Find a good breaking point (end of sentence or word)
      const truncated = cleanContent.substring(0, maxLength);
      const lastSpace = truncated.lastIndexOf(' ');
      const lastPeriod = truncated.lastIndexOf('.');
      
      // Use the better breaking point
      const breakPoint = Math.max(lastSpace, lastPeriod);
      if (breakPoint > maxLength * 0.7) { // Only use if it's not too short
        return cleanContent.substring(0, breakPoint) + '...';
      }
      
      return truncated + '...';
    };

    const messagePreview = getMessagePreview(message.content);
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
            <span className={`${styles.expandIcon} ${isExpanded ? styles.expanded : ''}`}>
              {isExpanded ? '-' : '+'}
            </span>
            <span className={styles.messagePreview}>{messagePreview}</span>
          </div>
          <div className={styles.headerRight}>
            {sessionName && (
              <span className={styles.sessionName}>{sessionName}</span>
            )}
          </div>
        </div>
        
        {/* Always show images (not collapsed) */}
        {imageResults.length > 0 && (
          <div className={styles.alwaysVisibleImages}>
            {imageResults.map((result, resultIndex) => (
              <div key={`image-${resultIndex}`} className={styles.imageContainer}>
                <MessageItemImageResult result={result} resultIndex={resultIndex} />
              </div>
            ))}
          </div>
        )}
        
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
            
            {/* Show non-image execution results only */}
            {message.execution_results && message.execution_results.length > 0 && (
              <div className={styles.results}>
                <strong>Results:</strong>
                {message.execution_results
                  .filter(result => !result.result?.image_url) // Exclude image results since they're shown above
                  .map((result, resultIndex) => (
                    <div key={resultIndex} className={`${styles.result} ${result.success ? styles.success : styles.failure}`}>
                      <div className={styles.resultHeader}>
                        {result.command} - {result.success ? '✅ Success' : '❌ Failed'}
                      </div>
                      <MessageItemImageResult result={result} resultIndex={resultIndex} />
                    </div>
                  ))
                }
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
            <div className={`${styles.messageContent} ${styles.resultContent}`}>
              {message.content}
            </div>
            
{message.image_url && (
              <div className={styles.jobImageContainer}>
                <ImageWithFallback 
                  src={getFullImageUrl(message.image_url)}
                  alt="Job Result"
                  className={styles.jobImage}
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