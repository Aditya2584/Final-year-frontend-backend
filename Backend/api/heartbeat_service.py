import base64
import io
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from lib.device import Camera
from lib.processors import findFaceGetPulse


@dataclass
class HeartbeatResult:
    bpm: float
    message: str
    plot_png_base64: Optional[str]
    series: Dict[str, Any]


def _make_plot_png_base64(times: List[float], samples: List[float], freqs_bpm: np.ndarray, fft: np.ndarray) -> str:
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


def run_heartbeat_capture(
    *,
    duration_sec: float = 15.0,
    camera_index: int = 0,
    warmup_sec: float = 1.5,
) -> HeartbeatResult:
    """
    Headless capture loop: opens webcam, runs pulse processor, returns BPM + plot.
    """
    cam = Camera(camera=camera_index)
    if not cam.valid:
        return HeartbeatResult(
            bpm=0.0,
            message="Camera not accessible. Check permissions / camera index.",
            plot_png_base64=None,
            series={},
        )

    processor = findFaceGetPulse(bpm_limits=[50, 180], data_spike_limit=2500.0, face_detector_smoothness=10.0)
    processor.find_faces = False  # go directly into tracking mode

    t_start = time.time()
    last_frame_time = t_start

    try:
        while True:
            now = time.time()
            if now - t_start >= duration_sec:
                break

            frame = cam.get_frame()
            processor.frame_in = frame
            processor.run(camera_index)

            # Prevent maxing CPU if camera fps is high
            dt = now - last_frame_time
            last_frame_time = now
            if dt < 1 / 60:
                time.sleep(0.001)
    finally:
        cam.release()

    bpm = float(getattr(processor, "bpm", 0.0) or 0.0)

    # Prefer first tracked face
    times: List[float] = []
    samples: List[float] = []
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

    # Drop warmup time from plotted series if possible
    if times and warmup_sec > 0:
        keep_idx = [i for i, t in enumerate(times) if t >= warmup_sec]
        if keep_idx:
            times = [times[i] for i in keep_idx]
            samples = [samples[i] for i in keep_idx if i < len(samples)]

    plot_b64 = None
    if len(times) >= 10 and len(samples) >= 10:
        plot_b64 = _make_plot_png_base64(times, samples, freqs_bpm, fft)

    if bpm <= 0:
        msg = "Could not estimate BPM yet. Ensure your face is visible and well-lit, then try again."
    else:
        msg = "Heartbeat captured successfully."

    return HeartbeatResult(
        bpm=bpm,
        message=msg,
        plot_png_base64=plot_b64,
        series={
            "times": times,
            "samples": samples,
        },
    )

