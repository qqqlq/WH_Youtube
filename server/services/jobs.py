import uuid
from typing import Dict, Any

# In-memory store for active rendering jobs
# key: job_id (str), value: dict with status and result data
# Example: {"status": "processing", "message": "Collecting assets...", "result": None}
_jobs: Dict[str, Dict[str, Any]] = {}

def create_job() -> str:
    """Create a new job and return its ID."""
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {
        "status": "pending",
        "message": "Job created, waiting to start...",
        "result": None
    }
    return job_id

def update_job(job_id: str, status: str, message: str = "", result: dict = None):
    """Update the status of an existing job."""
    if job_id in _jobs:
        _jobs[job_id]["status"] = status
        if message:
            _jobs[job_id]["message"] = message
        if result is not None:
            _jobs[job_id]["result"] = result

def get_job(job_id: str) -> Dict[str, Any]:
    """Retrieve the status of a job. Returns None if not found."""
    return _jobs.get(job_id)
