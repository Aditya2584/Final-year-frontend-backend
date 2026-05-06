import threading
import time
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any, Dict, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from api.heartbeat_service import run_heartbeat_capture
from api.frame_session import sessions
from api.db import init_db
from api.appointments import router as appointments_router


class HeartbeatStartRequest(BaseModel):
    duration_sec: float = Field(default=15.0, ge=5.0, le=60.0)
    camera_index: int = Field(default=0, ge=0, le=5)


class HeartbeatStartResponse(BaseModel):
    job_id: str
    status: str


class HeartbeatResultResponse(BaseModel):
    job_id: str
    status: str
    bpm: Optional[float] = None
    message: Optional[str] = None
    plot_png_base64: Optional[str] = None
    series: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


app = FastAPI(title="Heartbeat API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()
app.include_router(appointments_router)

_executor = ThreadPoolExecutor(max_workers=1)  # single camera session at a time
_camera_lock = threading.Lock()
_jobs: Dict[str, Future] = {}
_job_meta: Dict[str, Dict[str, Any]] = {}


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}

class HeartbeatSessionStartRequest(BaseModel):
    duration_sec: float = Field(default=12.0, ge=5.0, le=30.0)


class HeartbeatSessionStartResponse(BaseModel):
    session_id: str
    status: str


class HeartbeatSessionFrameResponse(BaseModel):
    status: str
    progress: float
    bpm: float
    heart_status: str


class HeartbeatSessionFinishResponse(BaseModel):
    status: str
    bpm: float
    heart_status: str
    message: str
    plot_png_base64: Optional[str] = None
    stats: Dict[str, Any]
    series: Optional[Dict[str, Any]] = None


@app.post("/api/heartbeat/session/start", response_model=HeartbeatSessionStartResponse)
def start_session(req: HeartbeatSessionStartRequest) -> HeartbeatSessionStartResponse:
    sess = sessions.create(duration_sec=req.duration_sec)
    return HeartbeatSessionStartResponse(session_id=sess.session_id, status="running")


@app.post("/api/heartbeat/session/{session_id}/frame", response_model=HeartbeatSessionFrameResponse)
async def push_frame(session_id: str, frame: UploadFile = File(...)) -> HeartbeatSessionFrameResponse:
    if not frame.content_type or "image" not in frame.content_type:
        raise HTTPException(status_code=400, detail="Frame must be an image.")
    data = await frame.read()
    try:
        payload = sessions.process_frame(session_id, data)
        return HeartbeatSessionFrameResponse(**payload)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/heartbeat/session/{session_id}/finish", response_model=HeartbeatSessionFinishResponse)
def finish_session(session_id: str) -> HeartbeatSessionFinishResponse:
    try:
        payload = sessions.finish(session_id)
        return HeartbeatSessionFinishResponse(**payload)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found.")


@app.post("/api/heartbeat/start", response_model=HeartbeatStartResponse)
def start_heartbeat(req: HeartbeatStartRequest) -> HeartbeatStartResponse:
    if _camera_lock.locked():
        raise HTTPException(status_code=409, detail="Heartbeat capture already running.")

    job_id = str(uuid.uuid4())
    _job_meta[job_id] = {"created_at": time.time()}

    def _run() -> Dict[str, Any]:
        with _camera_lock:
            res = run_heartbeat_capture(duration_sec=req.duration_sec, camera_index=req.camera_index)
            return {
                "bpm": res.bpm,
                "message": res.message,
                "plot_png_base64": res.plot_png_base64,
                "series": res.series,
            }

    _jobs[job_id] = _executor.submit(_run)
    return HeartbeatStartResponse(job_id=job_id, status="running")


@app.get("/api/heartbeat/{job_id}", response_model=HeartbeatResultResponse)
def get_heartbeat(job_id: str) -> HeartbeatResultResponse:
    fut = _jobs.get(job_id)
    if not fut:
        raise HTTPException(status_code=404, detail="Job not found.")

    if not fut.done():
        return HeartbeatResultResponse(job_id=job_id, status="running")

    try:
        payload = fut.result()
        return HeartbeatResultResponse(job_id=job_id, status="done", **payload)
    except Exception as e:
        return HeartbeatResultResponse(job_id=job_id, status="error", error=str(e))

