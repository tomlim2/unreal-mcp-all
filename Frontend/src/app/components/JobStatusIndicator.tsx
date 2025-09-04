"use client";

import React from 'react';
import styles from './JobStatusIndicator.module.css';
import { Job } from '../services/types';

interface JobStatusIndicatorProps {
  job: Job;
  showProgress?: boolean;
  compact?: boolean;
  className?: string;
}

const StatusIcon: React.FC<{ status: Job['status'] }> = ({ status }) => {
  switch (status) {
    case 'pending':
      return (
        <div className={styles.icon}>
          <svg className={styles.clock} fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
          </svg>
        </div>
      );

    case 'processing':
      return (
        <div className={styles.icon}>
          <div className={styles.spinner} />
        </div>
      );

    case 'completed':
      return (
        <div className={styles.icon}>
          <svg className={styles.checkmark} fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        </div>
      );

    case 'failed':
      return (
        <div className={styles.icon}>
          <svg className={styles.error} fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        </div>
      );

    case 'cancelled':
      return (
        <div className={styles.icon}>
          <svg className={styles.cancelled} fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
        </div>
      );

    default:
      return null;
  }
};

const getStatusText = (status: Job['status'], jobType: Job['job_type']): string => {
  switch (status) {
    case 'pending':
      return 'Pending';
    case 'processing':
      if (jobType === 'screenshot') return 'Taking screenshot...';
      if (jobType === 'batch_screenshot') return 'Processing batch...';
      return 'Processing...';
    case 'completed':
      return 'Completed';
    case 'failed':
      return 'Failed';
    case 'cancelled':
      return 'Cancelled';
    default:
      return 'Unknown';
  }
};

const JobStatusIndicator: React.FC<JobStatusIndicatorProps> = ({ 
  job, 
  showProgress = false, 
  compact = false, 
  className = '' 
}) => {
  const containerClasses = [
    styles.statusIndicator,
    styles[job.status],
    compact ? styles.compact : '',
    className
  ].filter(Boolean).join(' ');

  return (
    <div className={containerClasses}>
      <StatusIcon status={job.status} />
      <span className={styles.statusText}>
        {getStatusText(job.status, job.job_type)}
      </span>
      {showProgress && job.progress !== undefined && (
        <span className={styles.progress}>
          {Math.round(job.progress)}%
        </span>
      )}
    </div>
  );
};

export default JobStatusIndicator;