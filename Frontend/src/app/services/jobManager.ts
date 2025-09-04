import { Job, JobResponse } from './types';
import { getJobUpdateService } from './JobUpdateService';

export interface JobManagerCallbacks {
  onJobCreated?: (job: Job) => void;
  onJobUpdated?: (job: Job) => void;
  onJobCompleted?: (job: Job) => void;
  onJobFailed?: (job: Job, error: string) => void;
  onError?: (error: string) => void;
}

export class JobManager {
  private httpBridgePort: string;
  private callbacks: JobManagerCallbacks;
  private jobUpdateService = getJobUpdateService();

  constructor(callbacks: JobManagerCallbacks = {}) {
    this.httpBridgePort = process.env.NEXT_PUBLIC_HTTP_BRIDGE_PORT || '8080';
    this.callbacks = callbacks;
  }

  /**
   * Start a screenshot job
   */
  async startScreenshotJob(parameters: Record<string, unknown> = {}): Promise<Job | null> {
    try {
      // Extract session_id from parameters if present
      const { session_id, ...cleanParameters } = parameters;
      
      const response = await fetch(`http://localhost:${this.httpBridgePort}/api/screenshot/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          parameters: cleanParameters,
          session_id: session_id || null
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data: JobResponse = await response.json();

      if (!data.success || !data.job_id) {
        const error = data.error || 'Failed to start screenshot job';
        this.callbacks.onError?.(error);
        return null;
      }

      // Create initial job object
      const job: Job = {
        job_id: data.job_id,
        job_type: 'screenshot',
        status: 'pending',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        metadata: {
          parameters,
        },
      };

      // Call job created callback
      this.callbacks.onJobCreated?.(job);

      // Start polling for updates
      this.startPolling(job.job_id);

      return job;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      this.callbacks.onError?.(errorMessage);
      return null;
    }
  }

  /**
   * Get job status manually (one-time check)
   */
  async getJobStatus(jobId: string): Promise<Job | null> {
    try {
      return await this.jobUpdateService.checkJobStatus(jobId);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to get job status';
      this.callbacks.onError?.(errorMessage);
      return null;
    }
  }

  /**
   * Start polling for job updates
   */
  private startPolling(jobId: string): void {
    this.jobUpdateService.startPolling(
      jobId,
      // onUpdate
      (job: Job) => {
        this.callbacks.onJobUpdated?.(job);
      },
      // onComplete
      (job: Job) => {
        if (job.status === 'completed') {
          this.callbacks.onJobCompleted?.(job);
        } else if (job.status === 'failed') {
          this.callbacks.onJobFailed?.(job, job.error || 'Job failed');
        }
      },
      // onError
      (error: string) => {
        this.callbacks.onError?.(error);
      }
    );
  }

  /**
   * Stop polling for a specific job
   */
  stopPolling(jobId: string): void {
    this.jobUpdateService.stopPolling(jobId);
  }

  /**
   * Stop all active polling
   */
  stopAllPolling(): void {
    this.jobUpdateService.stopAllPolling();
  }

  /**
   * Check if currently polling for a job
   */
  isPolling(jobId: string): boolean {
    return this.jobUpdateService.isPolling(jobId);
  }

  /**
   * Get number of active polls
   */
  getActivePollCount(): number {
    return this.jobUpdateService.getActivePollCount();
  }

  /**
   * Update callbacks
   */
  setCallbacks(callbacks: JobManagerCallbacks): void {
    this.callbacks = { ...this.callbacks, ...callbacks };
  }

  /**
   * Download job result (for completed jobs with file results)
   */
  async downloadJobResult(job: Job): Promise<Blob | null> {
    if (job.status !== 'completed' || !job.result?.download_url) {
      return null;
    }

    try {
      const response = await fetch(job.result.download_url);
      if (!response.ok) {
        throw new Error(`Failed to download: ${response.statusText}`);
      }
      return await response.blob();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Download failed';
      this.callbacks.onError?.(errorMessage);
      return null;
    }
  }

  /**
   * Get job result URL (for completed jobs)
   */
  getJobResultUrl(job: Job): string | null {
    if (job.status !== 'completed' || !job.result?.download_url) {
      return null;
    }
    return job.result.download_url;
  }

  /**
   * Cancel a job (if supported by backend)
   */
  async cancelJob(jobId: string): Promise<boolean> {
    try {
      const response = await fetch(`http://localhost:${this.httpBridgePort}/api/screenshot/cancel/${jobId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      return data.success || false;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to cancel job';
      this.callbacks.onError?.(errorMessage);
      return false;
    }
  }
}

/**
 * Create a JobManager instance with callbacks
 */
export function createJobManager(callbacks: JobManagerCallbacks = {}): JobManager {
  return new JobManager(callbacks);
}