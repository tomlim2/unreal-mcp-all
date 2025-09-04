import { Job } from './types';

interface PollConfig {
  maxRetries: number;
  baseDelay: number;
  maxDelay: number;
  backoffMultiplier: number;
}

interface ActivePoll {
  jobId: string;
  retryCount: number;
  timeoutId: NodeJS.Timeout;
  onUpdate: (job: Job) => void;
  onComplete: (job: Job) => void;
  onError: (error: string) => void;
}

export class JobUpdateService {
  private activePolls: Map<string, ActivePoll> = new Map();
  private config: PollConfig;
  private httpBridgePort: string;

  constructor(config: Partial<PollConfig> = {}) {
    this.config = {
      maxRetries: 30,
      baseDelay: 1000, // 1 second
      maxDelay: 10000, // 10 seconds
      backoffMultiplier: 1.2,
      ...config,
    };
    this.httpBridgePort = process.env.NEXT_PUBLIC_HTTP_BRIDGE_PORT || '8080';
  }

  /**
   * Start polling for job status updates
   */
  startPolling(
    jobId: string,
    onUpdate: (job: Job) => void,
    onComplete: (job: Job) => void,
    onError: (error: string) => void
  ): void {
    // Stop existing poll if running
    this.stopPolling(jobId);

    const poll: ActivePoll = {
      jobId,
      retryCount: 0,
      timeoutId: setTimeout(() => {}, 0), // Will be set by pollOnce
      onUpdate,
      onComplete,
      onError,
    };

    this.activePolls.set(jobId, poll);
    this.pollOnce(poll);
  }

  /**
   * Stop polling for a specific job
   */
  stopPolling(jobId: string): void {
    const poll = this.activePolls.get(jobId);
    if (poll) {
      clearTimeout(poll.timeoutId);
      this.activePolls.delete(jobId);
    }
  }

  /**
   * Stop all active polling
   */
  stopAllPolling(): void {
    for (const poll of this.activePolls.values()) {
      clearTimeout(poll.timeoutId);
    }
    this.activePolls.clear();
  }

  /**
   * Get current active poll count
   */
  getActivePollCount(): number {
    return this.activePolls.size;
  }

  /**
   * Check if a job is currently being polled
   */
  isPolling(jobId: string): boolean {
    return this.activePolls.has(jobId);
  }

  private async pollOnce(poll: ActivePoll): Promise<void> {
    try {
      const job = await this.fetchJobStatus(poll.jobId);
      
      // Call update callback
      poll.onUpdate(job);

      // Check if job is complete
      if (job.status === 'completed' || job.status === 'failed') {
        this.activePolls.delete(poll.jobId);
        poll.onComplete(job);
        return;
      }

      // Check retry limit
      if (poll.retryCount >= this.config.maxRetries) {
        this.activePolls.delete(poll.jobId);
        poll.onError(`Job polling exceeded maximum retries (${this.config.maxRetries})`);
        return;
      }

      // Schedule next poll with exponential backoff
      const delay = Math.min(
        this.config.baseDelay * Math.pow(this.config.backoffMultiplier, poll.retryCount),
        this.config.maxDelay
      );

      poll.retryCount++;
      poll.timeoutId = setTimeout(() => this.pollOnce(poll), delay);

    } catch (error) {
      poll.retryCount++;

      // If we've exceeded retries, give up
      if (poll.retryCount >= this.config.maxRetries) {
        this.activePolls.delete(poll.jobId);
        poll.onError(`Failed to fetch job status: ${error instanceof Error ? error.message : 'Unknown error'}`);
        return;
      }

      // Otherwise, retry with backoff
      const delay = Math.min(
        this.config.baseDelay * Math.pow(this.config.backoffMultiplier, poll.retryCount),
        this.config.maxDelay
      );

      poll.timeoutId = setTimeout(() => this.pollOnce(poll), delay);
    }
  }

  private async fetchJobStatus(jobId: string): Promise<Job> {
    const response = await fetch(`http://localhost:${this.httpBridgePort}/api/screenshot/status/${jobId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    
    if (!data.success) {
      throw new Error(data.error || 'Failed to fetch job status');
    }

    return data.job;
  }

  /**
   * Manual job status check (one-time, no polling)
   */
  async checkJobStatus(jobId: string): Promise<Job> {
    return this.fetchJobStatus(jobId);
  }
}

// Singleton instance
let jobUpdateService: JobUpdateService | null = null;

/**
 * Get the singleton JobUpdateService instance
 */
export function getJobUpdateService(): JobUpdateService {
  if (!jobUpdateService) {
    jobUpdateService = new JobUpdateService();
  }
  return jobUpdateService;
}