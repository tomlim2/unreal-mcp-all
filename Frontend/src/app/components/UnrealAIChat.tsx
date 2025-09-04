"use client";

import { useState, useEffect, useCallback } from "react";
import styles from "./UnrealAIChat.module.css";
import { useJobStore } from "../store/jobStore";
import { createJobManager, Job } from "../services";
import JobMessage from "./JobMessage";
import type { JobManagerCallbacks } from "../services/jobManager";

interface UnrealLlmChatProps {
  loading: boolean;
  error: string | null;
  sessionId: string | null;
  llmFromDb: 'gemini' | 'gemini-2' | 'claude';
  onSubmit: (prompt: string, context: string, model?: string) => Promise<unknown>;
  onRefreshContext: () => void;
}

export default function UnrealLlmChat({
  loading,
  error,
  sessionId,
  llmFromDb,
  onSubmit,
  onRefreshContext,
}: UnrealLlmChatProps) {
  const [prompt, setPrompt] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [selectedLlm, setSelectedLlm] = useState<'gemini' | 'gemini-2' | 'claude'>(llmFromDb);
  
  // Job management
  const jobStore = useJobStore();
  const [jobManager, setJobManager] = useState<ReturnType<typeof createJobManager> | null>(null);

  useEffect(() => {
    setSelectedLlm(llmFromDb);
  }, [llmFromDb]);

  // Initialize job manager with callbacks
  useEffect(() => {
    const callbacks: JobManagerCallbacks = {
      onJobCreated: (job: Job) => {
        console.log('Job created:', job.job_id);
        jobStore.addJob(job);
      },
      onJobUpdated: (job: Job) => {
        console.log('Job updated:', job.job_id, job.status);
        jobStore.updateJob(job);
      },
      onJobCompleted: (job: Job) => {
        console.log('Job completed:', job.job_id);
        jobStore.updateJob(job);
      },
      onJobFailed: (job: Job, error: string) => {
        console.error('Job failed:', job.job_id, error);
        jobStore.updateJob(job);
      },
      onError: (error: string) => {
        console.error('Job error:', error);
      },
    };

    const manager = createJobManager(callbacks);
    setJobManager(manager);

    return () => {
      manager.stopAllPolling();
    };
  }, [jobStore]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    setSubmitting(true);

    try {
      // Check if this is a screenshot request
      const isScreenshotRequest = prompt.toLowerCase().includes('screenshot') || 
                                  prompt.toLowerCase().includes('high-res') ||
                                  prompt.toLowerCase().includes('capture');

      if (isScreenshotRequest && jobManager) {
        // Handle as a job
        console.log('Starting screenshot job...');
        const job = await jobManager.startScreenshotJob({
          original_prompt: prompt,
          session_id: sessionId,
          model: selectedLlm
        });
        
        if (job) {
          console.log('Screenshot job started:', job.job_id);
        }
      } else {
        // Handle as regular chat
        const data = await onSubmit(
          prompt,
          "User is a creative cinema director",
          selectedLlm
        );

        console.log("AI Response:", data);
      }

      onRefreshContext();
      setPrompt(""); // Clear the input after successful submission
    } catch (err) {
      // Error is handled by parent component
      console.error('Submit failed:', err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleExamplePrompt = (examplePrompt: string) => {
    setPrompt(examplePrompt);
  };

  // Job action handlers
  const handleJobCancel = useCallback(async (jobId: string) => {
    if (jobManager) {
      const success = await jobManager.cancelJob(jobId);
      if (success) {
        jobManager.stopPolling(jobId);
        jobStore.removeJob(jobId);
      }
    }
  }, [jobManager, jobStore]);

  const handleJobRetry = useCallback(async (jobId: string) => {
    const job = jobStore.getJob(jobId);
    if (job?.metadata?.original_prompt && jobManager) {
      await jobManager.startScreenshotJob(job.metadata.parameters || {});
      jobStore.removeJob(jobId);
    }
  }, [jobManager, jobStore]);

  const handleJobDownload = useCallback(async (job: Job) => {
    if (jobManager) {
      const blob = await jobManager.downloadJobResult(job);
      if (blob) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = job.result?.filename || `screenshot-${job.job_id}.png`;
        a.click();
        URL.revokeObjectURL(url);
      }
    }
  }, [jobManager]);

  const handleJobRemove = useCallback((jobId: string) => {
    jobStore.removeJob(jobId);
  }, [jobStore]);

  // Determine if actions should be disabled
  const isProcessing = loading || submitting || jobStore.state.isProcessing;
  const activeJobs = jobStore.getActiveJobs();
  const completedJobs = jobStore.getCompletedJobs();

  const examplePrompts = [
    "Set the time to sunrise (6 AM)",
    "Show me all actors in the current level",
    "Set the sky to sunset time",
    "Set to San Francisco",
    "Set the New York City",
    "Move the map to Tokyo Japan",
    "Create a bright white light at position 0,0,200",
    "Create a warm orange light named MainLight",
    "Show me all MM control lights",
    "Make MainLight red and move it to 100,100,150",
    "Delete the light named MainLight",
    "Take a high-resolution screenshot",
    "Make it rain and take a screenshot",
  ];

  return (
    <>
      <div className={styles.container}>
        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.inputGroup}>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  if (!isProcessing && prompt.trim()) {
                    const form = e.currentTarget.form;
                    if (form) {
                      form.requestSubmit();
                    }
                  }
                }
              }}
              placeholder="Describe what you want to do in Unreal Engine... (Press Enter to execute, Shift+Enter for new line)"
              className={styles.textarea}
              rows={3}
            />
            <button
              type="submit"
              disabled={isProcessing || !prompt.trim()}
              className={styles.submitButton}
            >
              {isProcessing ? "Processing..." : "Execute"}
            </button>
          </div>
        </form>
		<div className={styles.modelSwitcher}>
        <label htmlFor="model-select" className={styles.modelLabel}>
          AI Model: {sessionId && `(Session: ${sessionId.slice(-8)})`}
        </label>
        <select
          id="model-select"
          value={selectedLlm}
          onChange={(e) => setSelectedLlm(e.target.value as 'gemini' | 'gemini-2' | 'claude')}
          className={styles.modelSelect}
          disabled={isProcessing}
        >
			<option value="gemini">gemini-1.5-flash</option>
            <option value="gemini-2">gemini-2.5-flash</option>
            <option value="claude">claude-3-haiku-20240307</option>
        </select>
      </div>
      </div>
      <div className={styles.examples}>
        <h3>Examples:</h3>
        <div className={styles.exampleButtons}>
          {examplePrompts.map((example, index) => (
            <button
              key={index}
              onClick={() => handleExamplePrompt(example)}
              className={styles.exampleButton}
              disabled={isProcessing}
            >
              {example}
            </button>
          ))}
        </div>
      </div>
      
      {/* Active Jobs Section */}
      {activeJobs.length > 0 && (
        <div className={styles.jobsSection}>
          <h3 className={styles.jobsSectionTitle}>Active Jobs</h3>
          {activeJobs.map(job => (
            <JobMessage
              key={job.job_id}
              job={job}
              onCancel={handleJobCancel}
              onRetry={handleJobRetry}
              onDownload={handleJobDownload}
              onRemove={handleJobRemove}
            />
          ))}
        </div>
      )}
      
      {/* Completed Jobs Section */}
      {completedJobs.length > 0 && (
        <div className={styles.jobsSection}>
          <div className={styles.jobsSectionHeader}>
            <h3 className={styles.jobsSectionTitle}>Recent Jobs</h3>
            <button
              onClick={jobStore.clearCompletedJobs}
              className={styles.clearJobsButton}
            >
              Clear All
            </button>
          </div>
          {completedJobs.slice(0, 5).map(job => (
            <JobMessage
              key={job.job_id}
              job={job}
              onRetry={handleJobRetry}
              onDownload={handleJobDownload}
              onRemove={handleJobRemove}
              showActions={job.status === 'failed' || job.status === 'completed'}
            />
          ))}
        </div>
      )}
    </>
  );
}