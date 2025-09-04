"use client";

import React, { useState } from 'react';
import styles from './JobMessage.module.css';
import JobStatusIndicator from './JobStatusIndicator';
import { Job } from '../services/types';

interface JobMessageProps {
  job: Job;
  onCancel?: (jobId: string) => void;
  onRetry?: (jobId: string) => void;
  onDownload?: (job: Job) => void;
  onRemove?: (jobId: string) => void;
  showActions?: boolean;
  className?: string;
}

const JobMessage: React.FC<JobMessageProps> = ({
  job,
  onCancel,
  onRetry,
  onDownload,
  onRemove,
  showActions = true,
  className = ''
}) => {
  const [imageError, setImageError] = useState(false);

  const formatFileSize = (bytes: number): string => {
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;

    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }

    return `${size.toFixed(unitIndex > 0 ? 1 : 0)} ${units[unitIndex]}`;
  };

  const formatTimestamp = (timestamp: string): string => {
    return new Date(timestamp).toLocaleString();
  };

  const getJobTypeDisplay = (jobType: Job['job_type']): string => {
    switch (jobType) {
      case 'screenshot':
        return 'Screenshot';
      case 'batch_screenshot':
        return 'Batch Screenshot';
      default:
        return jobType;
    }
  };

  const containerClasses = [
    styles.jobMessage,
    styles[job.status],
    className
  ].filter(Boolean).join(' ');

  const canCancel = job.status === 'pending' || job.status === 'processing';
  const canRetry = job.status === 'failed' || job.status === 'cancelled';
  const canDownload = job.status === 'completed' && job.result?.download_url;
  const canRemove = job.status === 'completed' || job.status === 'failed' || job.status === 'cancelled';

  return (
    <div className={containerClasses}>
      <div className={styles.header}>
        <div className={styles.jobInfo}>
          <div className={styles.jobTitle}>
            {getJobTypeDisplay(job.job_type)}
          </div>
          <JobStatusIndicator job={job} showProgress compact />
          <div className={styles.jobId}>
            {job.job_id.slice(0, 8)}...
          </div>
        </div>
        
        {showActions && (
          <div className={styles.actions}>
            {canCancel && onCancel && (
              <button
                className={`${styles.actionButton} ${styles.danger}`}
                onClick={() => onCancel(job.job_id)}
                title="Cancel Job"
              >
                Cancel
              </button>
            )}
            
            {canRetry && onRetry && (
              <button
                className={`${styles.actionButton} ${styles.primary}`}
                onClick={() => onRetry(job.job_id)}
                title="Retry Job"
              >
                Retry
              </button>
            )}
            
            {canDownload && onDownload && (
              <button
                className={`${styles.actionButton} ${styles.primary}`}
                onClick={() => onDownload(job)}
                title="Download Result"
              >
                Download
              </button>
            )}
            
            {canRemove && onRemove && (
              <button
                className={styles.actionButton}
                onClick={() => onRemove(job.job_id)}
                title="Remove from List"
              >
                Remove
              </button>
            )}
          </div>
        )}
      </div>

      <div className={styles.details}>
        <div className={styles.metadata}>
          <div className={styles.metadataItem}>
            <span>Created:</span>
            <span>{formatTimestamp(job.created_at)}</span>
          </div>
          <div className={styles.metadataItem}>
            <span>Updated:</span>
            <span>{formatTimestamp(job.updated_at)}</span>
          </div>
          {job.metadata?.original_prompt && (
            <div className={styles.metadataItem}>
              <span>Prompt:</span>
              <span>"{job.metadata.original_prompt}"</span>
            </div>
          )}
        </div>

        {/* Progress bar for processing jobs */}
        {job.status === 'processing' && job.progress !== undefined && (
          <div className={styles.progressSection}>
            <div className={styles.progressBar}>
              <div 
                className={styles.progressFill}
                style={{ width: `${job.progress}%` }}
              />
            </div>
            <div className={styles.progressText}>
              {Math.round(job.progress)}%
            </div>
          </div>
        )}

        {/* Result section for completed jobs */}
        {job.status === 'completed' && job.result && (
          <div className={styles.resultSection}>
            <div className={styles.resultTitle}>Result</div>
            <div className={styles.resultContent}>
              <div className={styles.fileInfo}>
                {job.result.filename && (
                  <div className={styles.fileInfoItem}>
                    <div className={styles.fileInfoLabel}>Filename</div>
                    <div className={styles.fileInfoValue}>{job.result.filename}</div>
                  </div>
                )}
                
                {job.result.file_size && (
                  <div className={styles.fileInfoItem}>
                    <div className={styles.fileInfoLabel}>Size</div>
                    <div className={styles.fileInfoValue}>
                      {formatFileSize(job.result.file_size)}
                    </div>
                  </div>
                )}
                
                {job.result.file_path && (
                  <div className={styles.fileInfoItem}>
                    <div className={styles.fileInfoLabel}>Path</div>
                    <div className={styles.fileInfoValue}>{job.result.file_path}</div>
                  </div>
                )}
              </div>
              
              {/* Thumbnail preview */}
              {job.result.thumbnail_url && !imageError && (
                <img
                  src={job.result.thumbnail_url}
                  alt="Screenshot thumbnail"
                  className={styles.thumbnail}
                  onError={() => setImageError(true)}
                  onClick={() => job.result?.download_url && window.open(job.result.download_url, '_blank')}
                />
              )}
              
              {/* Download link */}
              {job.result.download_url && (
                <div>
                  <a
                    href={job.result.download_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={styles.downloadLink}
                  >
                    Open full image
                  </a>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Error section for failed jobs */}
        {job.status === 'failed' && job.error && (
          <div className={styles.errorSection}>
            <div className={styles.resultTitle}>Error</div>
            <div className={styles.errorText}>{job.error}</div>
          </div>
        )}
      </div>
    </div>
  );
};

export default JobMessage;