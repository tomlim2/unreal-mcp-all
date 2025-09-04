"""
Job Manager for handling long-running tasks.

Provides job queuing, status tracking, and result storage using Supabase.
"""

import uuid
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass, asdict

# Configure logging
logger = logging.getLogger("JobManager")

class JobStatus(Enum):
    """Job execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class JobResult:
    """Job execution result."""
    filename: Optional[str] = None
    filepath: Optional[str] = None
    download_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    file_size: Optional[int] = None
    resolution: Optional[Dict[str, int]] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass 
class Job:
    """Represents a job in the system."""
    job_id: str
    job_type: str
    session_id: Optional[str]
    status: JobStatus
    params: Dict[str, Any]
    result: Optional[JobResult] = None
    error: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'job_id': self.job_id,
            'job_type': self.job_type,
            'session_id': self.session_id,
            'status': self.status.value,
            'params': self.params,
            'result': asdict(self.result) if self.result else None,
            'error': self.error,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class JobManager:
    """Manages job lifecycle and storage."""
    
    def __init__(self, supabase_client=None):
        """Initialize job manager."""
        self.supabase = supabase_client
        self.jobs_table = "screenshot_jobs"
        
        # In-memory job cache for quick access
        self._job_cache: Dict[str, Job] = {}
        
        logger.info("JobManager initialized")

    def create_job(self, job_type: str, params: Dict[str, Any], session_id: Optional[str] = None) -> str:
        """Create a new job and return job ID."""
        job_id = str(uuid.uuid4())
        
        job = Job(
            job_id=job_id,
            job_type=job_type,
            session_id=session_id,
            status=JobStatus.PENDING,
            params=params
        )
        
        # Store in cache
        self._job_cache[job_id] = job
        
        # Store in database if available
        if self.supabase:
            try:
                self.supabase.table(self.jobs_table).insert({
                    'job_id': job_id,
                    'job_type': job_type,
                    'session_id': session_id,
                    'status': JobStatus.PENDING.value,
                    'params': params,
                    'created_at': job.created_at.isoformat(),
                    'updated_at': job.updated_at.isoformat()
                }).execute()
                
                logger.info(f"Created job {job_id} of type {job_type}")
            except Exception as e:
                logger.error(f"Failed to store job in database: {e}")
        
        return job_id

    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        # Try cache first
        if job_id in self._job_cache:
            return self._job_cache[job_id]
        
        # Try database
        if self.supabase:
            try:
                response = self.supabase.table(self.jobs_table).select("*").eq('job_id', job_id).execute()
                
                if response.data:
                    job_data = response.data[0]
                    job = Job(
                        job_id=job_data['job_id'],
                        job_type=job_data['job_type'],
                        session_id=job_data.get('session_id'),
                        status=JobStatus(job_data['status']),
                        params=job_data.get('params', {}),
                        result=JobResult(**job_data['result']) if job_data.get('result') else None,
                        error=job_data.get('error'),
                        created_at=datetime.fromisoformat(job_data['created_at']),
                        updated_at=datetime.fromisoformat(job_data['updated_at']) if job_data.get('updated_at') else None
                    )
                    
                    # Cache it
                    self._job_cache[job_id] = job
                    return job
                    
            except Exception as e:
                logger.error(f"Failed to get job {job_id} from database: {e}")
        
        return None

    def update_job_status(self, job_id: str, status: JobStatus, result: Optional[JobResult] = None, error: Optional[str] = None) -> bool:
        """Update job status and result."""
        job = self.get_job(job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return False
        
        # Update job object
        job.status = status
        job.updated_at = datetime.now()
        
        if result:
            job.result = result
        if error:
            job.error = error
        
        # Update cache
        self._job_cache[job_id] = job
        
        # Update database
        if self.supabase:
            try:
                update_data = {
                    'status': status.value,
                    'updated_at': job.updated_at.isoformat()
                }
                
                if result:
                    update_data['result'] = asdict(result)
                if error:
                    update_data['error'] = error
                
                self.supabase.table(self.jobs_table).update(update_data).eq('job_id', job_id).execute()
                
                logger.info(f"Updated job {job_id} status to {status.value}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to update job {job_id} in database: {e}")
        
        return True

    def list_active_jobs(self, session_id: Optional[str] = None) -> List[Job]:
        """List all active jobs, optionally filtered by session."""
        active_statuses = [JobStatus.PENDING, JobStatus.IN_PROGRESS]
        
        if self.supabase:
            try:
                query = self.supabase.table(self.jobs_table).select("*").in_('status', [s.value for s in active_statuses])
                
                if session_id:
                    query = query.eq('session_id', session_id)
                
                response = query.execute()
                
                jobs = []
                for job_data in response.data:
                    job = Job(
                        job_id=job_data['job_id'],
                        job_type=job_data['job_type'],
                        session_id=job_data.get('session_id'),
                        status=JobStatus(job_data['status']),
                        params=job_data.get('params', {}),
                        result=JobResult(**job_data['result']) if job_data.get('result') else None,
                        error=job_data.get('error'),
                        created_at=datetime.fromisoformat(job_data['created_at']),
                        updated_at=datetime.fromisoformat(job_data['updated_at']) if job_data.get('updated_at') else None
                    )
                    jobs.append(job)
                    
                    # Update cache
                    self._job_cache[job.job_id] = job
                
                return jobs
                
            except Exception as e:
                logger.error(f"Failed to list active jobs: {e}")
        
        # Fallback to cache
        return [job for job in self._job_cache.values() if job.status in active_statuses]

    def cleanup_old_jobs(self, max_age_days: int = 7) -> int:
        """Clean up old completed/failed jobs."""
        if not self.supabase:
            return 0
        
        try:
            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            
            response = self.supabase.table(self.jobs_table).delete().in_(
                'status', [JobStatus.COMPLETED.value, JobStatus.FAILED.value, JobStatus.CANCELLED.value]
            ).lt('updated_at', cutoff_date.isoformat()).execute()
            
            count = len(response.data) if response.data else 0
            logger.info(f"Cleaned up {count} old jobs")
            
            # Clear cache entries for deleted jobs
            for job_id in list(self._job_cache.keys()):
                job = self._job_cache[job_id]
                if (job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED] and 
                    job.updated_at < cutoff_date):
                    del self._job_cache[job_id]
            
            return count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old jobs: {e}")
            return 0

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job."""
        job = self.get_job(job_id)
        if not job:
            return False
        
        if job.status not in [JobStatus.PENDING, JobStatus.IN_PROGRESS]:
            logger.warning(f"Cannot cancel job {job_id} with status {job.status}")
            return False
        
        return self.update_job_status(job_id, JobStatus.CANCELLED)