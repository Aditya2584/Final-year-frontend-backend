import base64
import io
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional

import cv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from lib.processors import findFaceGetPulse


def _make_plot_png_base64(times, samples, freqs_bpm: np.ndarray, fft: np.ndarray) -> Optional[str]:
    if not times or not samples or len(times) < 10 or len(samples) < 10:
        return None

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 4.8), dpi=160)
    fig.patch.set_facecolor("white")

    ax1.plot(times, samples, color="#0ea5e9", linewidth=1.5)
    ax1.set_title("Raw forehead signal", fontsize=10)
    ax1.set_xlabel("Time (s)", fontsize=9)
    ax1.set_ylabel("Intensity", fontsize=9)
    ax1.grid(True, alpha=0.2)

    if freqs_bpm.size and fft.size:
        ax2.plot(freqs_bpm, fft, color="#0f172a", linewidth=1.5)
        ax2.set_title("Frequency spectrum", fontsize=10)
        ax2.set_xlabel("BPM", fontsize=9)
        ax2.set_ylabel("Power", fontsize=9)
        ax2.grid(True, alpha=0.2)
    else:
        ax2.text(0.5, 0.5, "Not enough data for FFT yet", ha="center", va="center")
        ax2.set_axis_off()

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def _heart_status(bpm: float) -> str:
    if bpm <= 0:
        return "unknown"
    if bpm < 60:
        return "low"
    if bpm <= 100:
        return "normal"
    return "high"


@dataclass
class HeartbeatSession:
    session_id: str
    created_at: float
    duration_sec: float
    processor: findFaceGetPulse
    last_bpm: float = 0.0
    frames: int = 0


class SessionManager:
    def __init__(self):
        self._sessions: Dict[str, HeartbeatSession] = {}

    def create(self, *, duration_sec: float) -> HeartbeatSession:
        sid = str(uuid.uuid4())
        processor = findFaceGetPulse(bpm_limits=[50, 180], data_spike_limit=2500.0, face_detector_smoothness=10.0)
        processor.find_faces = False  # tracking mode (no GUI)
        sess = HeartbeatSession(session_id=sid, created_at=time.time(), duration_sec=duration_sec, processor=processor)
        self._sessions[sid] = sess
        return sess

    def get(self, session_id: str) -> Optional[HeartbeatSession]:
        return self._sessions.get(session_id)

    def delete(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def process_frame(self, session_id: str, jpeg_bytes: bytes) -> Dict[str, Any]:
        sess = self.get(session_id)
        if not sess:
            raise KeyError("Session not found")

        now = time.time()
        elapsed = now - sess.created_at

        arr = np.frombuffer(jpeg_bytes, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError("Invalid image frame")

        sess.processor.frame_in = frame
        sess.processor.run(0)

        bpm = float(getattr(sess.processor, "bpm", 0.0) or 0.0)
        if bpm > 0:
            sess.last_bpm = bpm
        sess.frames += 1

        progress = min(1.0, max(0.0, elapsed / sess.duration_sec))
        return {
            "status": "running" if progress < 1.0 else "done",
            "progress": progress,
            "bpm": sess.last_bpm if sess.last_bpm > 0 else bpm,
            "heart_status": _heart_status(sess.last_bpm if sess.last_bpm > 0 else bpm),
        }

    def finish(self, session_id: str) -> Dict[str, Any]:
        sess = self.get(session_id)
        if not sess:
            raise KeyError("Session not found")

        processor = sess.processor
        bpm = float(getattr(processor, "bpm", 0.0) or 0.0) or sess.last_bpm

        times = []
        samples = []
        freqs_bpm = np.array([])
        fft = np.array([])

        if getattr(processor, "face_trackers", None):
            first_tracker = list(processor.face_trackers.values())[0]
            times = list(getattr(first_tracker, "times", []))
            samples = list(getattr(first_tracker, "samples", []))
            freqs_bpm = np.array(getattr(first_tracker, "freqs", np.array([])))
            fft = np.array(getattr(first_tracker, "fft", np.array([])))
        else:
            times = list(getattr(processor, "times", []))
            samples = list(getattr(processor, "samples", []))
            freqs_bpm = np.array(getattr(processor, "freqs", np.array([])))
            fft = np.array(getattr(processor, "fft", np.array([])))

        plot_png_base64 = _make_plot_png_base64(times, samples, freqs_bpm, fft)

        if bpm and bpm > 0:
            message = "Scan complete."
        else:
            message = "Scan complete, but BPM could not be estimated. Try better lighting and keep your face still."

        payload = {
            "status": "done",
            "bpm": bpm,
            "heart_status": _heart_status(bpm),
            "message": message,
            "plot_png_base64": plot_png_base64,
            "stats": {
                "frames_processed": sess.frames,
                "duration_sec": sess.duration_sec,
            },
            "series": {"times": times, "samples": samples},
        }

        self.delete(session_id)
        return payload


sessions = SessionManager()

