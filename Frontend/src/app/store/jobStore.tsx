"use client";

import { createContext, useContext, useReducer, ReactNode } from 'react';
import { Job } from '../services/types';

// Job Store Types
interface JobState {
  jobs: Record<string, Job>;
  activeJobs: string[];
  isProcessing: boolean;
}

type JobAction =
  | { type: 'ADD_JOB'; payload: Job }
  | { type: 'UPDATE_JOB'; payload: Job }
  | { type: 'REMOVE_JOB'; payload: string }
  | { type: 'CLEAR_COMPLETED_JOBS' }
  | { type: 'SET_PROCESSING'; payload: boolean };

interface JobContextType {
  state: JobState;
  dispatch: (action: JobAction) => void;
  // Helper methods
  addJob: (job: Job) => void;
  updateJob: (job: Job) => void;
  removeJob: (jobId: string) => void;
  clearCompletedJobs: () => void;
  setProcessing: (processing: boolean) => void;
  getJob: (jobId: string) => Job | undefined;
  hasActiveJobs: () => boolean;
  getActiveJobs: () => Job[];
  getCompletedJobs: () => Job[];
}

// Initial state
const initialState: JobState = {
  jobs: {},
  activeJobs: [],
  isProcessing: false,
};

// Reducer
function jobReducer(state: JobState, action: JobAction): JobState {
  switch (action.type) {
    case 'ADD_JOB':
      return {
        ...state,
        jobs: {
          ...state.jobs,
          [action.payload.job_id]: action.payload,
        },
        activeJobs: [...state.activeJobs, action.payload.job_id],
        isProcessing: true,
      };

    case 'UPDATE_JOB': {
      const updatedJob = action.payload;
      const isCompleted = updatedJob.status === 'completed' || updatedJob.status === 'failed' || updatedJob.status === 'cancelled';
      
      return {
        ...state,
        jobs: {
          ...state.jobs,
          [updatedJob.job_id]: updatedJob,
        },
        activeJobs: isCompleted 
          ? state.activeJobs.filter(id => id !== updatedJob.job_id)
          : state.activeJobs,
        isProcessing: state.activeJobs.length > (isCompleted ? 1 : 0),
      };
    }

    case 'REMOVE_JOB': {
      const { [action.payload]: removedJob, ...remainingJobs } = state.jobs;
      return {
        ...state,
        jobs: remainingJobs,
        activeJobs: state.activeJobs.filter(id => id !== action.payload),
        isProcessing: state.activeJobs.length > 1,
      };
    }

    case 'CLEAR_COMPLETED_JOBS': {
      const activeJobs = Object.values(state.jobs).filter(
        job => job.status === 'pending' || job.status === 'in_progress'
      );
      const activeJobsRecord = activeJobs.reduce((acc, job) => {
        acc[job.job_id] = job;
        return acc;
      }, {} as Record<string, Job>);

      return {
        ...state,
        jobs: activeJobsRecord,
        activeJobs: activeJobs.map(job => job.job_id),
        isProcessing: activeJobs.length > 0,
      };
    }

    case 'SET_PROCESSING':
      return {
        ...state,
        isProcessing: action.payload,
      };

    default:
      return state;
  }
}

// Context
const JobContext = createContext<JobContextType | undefined>(undefined);

// Provider component
export function JobProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(jobReducer, initialState);

  const contextValue: JobContextType = {
    state,
    dispatch,
    addJob: (job: Job) => dispatch({ type: 'ADD_JOB', payload: job }),
    updateJob: (job: Job) => dispatch({ type: 'UPDATE_JOB', payload: job }),
    removeJob: (jobId: string) => dispatch({ type: 'REMOVE_JOB', payload: jobId }),
    clearCompletedJobs: () => dispatch({ type: 'CLEAR_COMPLETED_JOBS' }),
    setProcessing: (processing: boolean) => dispatch({ type: 'SET_PROCESSING', payload: processing }),
    getJob: (jobId: string) => state.jobs[jobId],
    hasActiveJobs: () => state.activeJobs.length > 0,
    getActiveJobs: () => state.activeJobs.map(id => state.jobs[id]).filter(Boolean),
    getCompletedJobs: () => Object.values(state.jobs).filter(
      job => job.status === 'completed' || job.status === 'failed' || job.status === 'cancelled'
    ),
  };

  return (
    <JobContext.Provider value={contextValue}>
      {children}
    </JobContext.Provider>
  );
}

// Hook to use job context
export function useJobStore(): JobContextType {
  const context = useContext(JobContext);
  if (context === undefined) {
    throw new Error('useJobStore must be used within a JobProvider');
  }
  return context;
}