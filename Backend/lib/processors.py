import numpy as np
import time
import cv2
import pylab
import os
import sys
from typing import List, Tuple, Optional, Union, Any, Dict
from collections import defaultdict


def resource_path(relative_path: str) -> str:
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # In dev, resolve relative to the backend project root (not the process cwd)
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    return os.path.join(base_path, relative_path)


class FaceTracker:
    """Tracks individual face data and calculates BPM for a single face"""
    
    def __init__(self, face_id: int, face_rect: List[int], buffer_size: int = 250):
        self.face_id = face_id
        self.face_rect = face_rect
        self.buffer_size = buffer_size
        self.data_buffer: List[float] = []
        self.times: List[float] = []
        self.bpm = 0.0
        self.last_center = np.array([face_rect[0] + 0.5 * face_rect[2], 
                                     face_rect[1] + 0.5 * face_rect[3]])
        self.last_update = time.time()
        self.fps = 0
        self.freqs: np.ndarray = np.array([])
        self.fft: np.ndarray = np.array([])
        self.samples: List[float] = []
        self.idx = 1
        self.t0 = time.time()
        # Different colors for different faces
        self.colors = [
            (0, 255, 0),    # Green
            (255, 0, 0),    # Blue
            (0, 0, 255),    # Red
            (255, 255, 0),  # Cyan
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Yellow
        ]
        self.color = self.colors[face_id % len(self.colors)]
        
    def update_face_rect(self, face_rect: List[int]) -> None:
        """Update face rectangle and center"""
        self.face_rect = face_rect
        self.last_center = np.array([face_rect[0] + 0.5 * face_rect[2], 
                                     face_rect[1] + 0.5 * face_rect[3]])
        self.last_update = time.time()
    
    def get_center(self) -> np.ndarray:
        """Get center point of face"""
        x, y, w, h = self.face_rect
        return np.array([x + 0.5 * w, y + 0.5 * h])
    
    def calculate_distance(self, other_rect: List[int]) -> float:
        """Calculate distance to another face rectangle"""
        x, y, w, h = other_rect
        other_center = np.array([x + 0.5 * w, y + 0.5 * h])
        return np.linalg.norm(self.last_center - other_center)
    
    def get_subface_coord(self, fh_x: float, fh_y: float, fh_w: float, fh_h: float) -> List[int]:
        """Get forehead coordinates relative to face"""
        x, y, w, h = self.face_rect
        return [int(x + w * fh_x - (w * fh_w / 2.0)),
                int(y + h * fh_y - (h * fh_h / 2.0)),
                int(w * fh_w),
                int(h * fh_h)]
    
    def get_subface_means(self, coord: List[int], frame: np.ndarray) -> float:
        """Get mean intensity from forehead region"""
        x, y, w, h = coord
        # Ensure coordinates are within frame bounds
        h_frame, w_frame = frame.shape[:2]
        x = max(0, min(x, w_frame - 1))
        y = max(0, min(y, h_frame - 1))
        w = min(w, w_frame - x)
        h = min(h, h_frame - y)
        
        if w <= 0 or h <= 0:
            return 0.0
            
        subframe = frame[y:y + h, x:x + w, :]
        if subframe.size == 0:
            return 0.0
            
        v1 = np.mean(subframe[:, :, 0])
        v2 = np.mean(subframe[:, :, 1])
        v3 = np.mean(subframe[:, :, 2])
        return (v1 + v2 + v3) / 3.
    
    def process_frame(self, frame: np.ndarray, gray: np.ndarray, current_time: float) -> None:
        """Process a frame and update BPM calculation"""
        # current_time is already relative to processor's t0, so use it directly
        self.times.append(current_time)
        
        forehead = self.get_subface_coord(0.5, 0.18, 0.25, 0.15)
        vals = self.get_subface_means(forehead, frame)
        
        self.data_buffer.append(vals)
        L = len(self.data_buffer)
        
        if L > self.buffer_size:
            self.data_buffer = self.data_buffer[-self.buffer_size:]
            self.times = self.times[-self.buffer_size:]
            L = self.buffer_size
        
        if L > 10:
            processed = np.array(self.data_buffer)
            self.samples = processed.tolist()
            
            self.fps = float(L) / (self.times[-1] - self.times[0]) if self.times[-1] != self.times[0] else 30.0
            
            even_times = np.linspace(self.times[0], self.times[-1], L)
            interpolated = np.interp(even_times, self.times, processed)
            interpolated = np.hamming(L) * interpolated
            interpolated = interpolated - np.mean(interpolated)
            raw = np.fft.rfft(interpolated)
            phase = np.angle(raw)
            self.fft = np.abs(raw)
            self.freqs = float(self.fps) / L * np.arange(L // 2 + 1)
            
            freqs = 60. * self.freqs
            idx = np.where((freqs > 50) & (freqs < 180))
            
            if len(idx[0]) > 0:
                pruned = self.fft[idx]
                phase = phase[idx]
                pfreq = freqs[idx]
                self.freqs = pfreq
                self.fft = pruned
                
                if pruned.size > 0:
                    idx2 = np.argmax(pruned)
                    self.bpm = self.freqs[idx2]
                else:
                    self.bpm = 0.0
            else:
                self.bpm = 0.0


class findFaceGetPulse:

    def __init__(self, bpm_limits: List[int] = None, data_spike_limit: float = 250,
                 face_detector_smoothness: float = 10):
        if bpm_limits is None:
            bpm_limits = []
            
        self.frame_in = np.zeros((10, 10))
        self.frame_out = np.zeros((10, 10))
        self.fps = 0
        self.buffer_size = 250
        self.times: List[float] = []
        self.slices: List[List[Any]] = [[0]]
        self.t0 = time.time()
        self.bpm = 0  # Keep for backward compatibility
        
        dpath = resource_path("haarcascade_frontalface_alt.xml")
        if not os.path.exists(dpath):
            print("Cascade file not present!")
        self.face_cascade = cv2.CascadeClassifier(dpath)

        # Multi-face tracking
        self.face_trackers: Dict[int, FaceTracker] = {}
        self.next_face_id = 0
        self.max_face_distance = 100  # Maximum distance to match faces across frames
        self.face_timeout = 2.0  # Seconds before removing a face that's not detected
        
        self.output_dim = 13
        self.trained = False
        self.pcadata = None

        self.idx = 1
        self.find_faces = True

    def find_faces_toggle(self) -> bool:
        self.find_faces = not self.find_faces
        if self.find_faces:
            # Reset all trackers when restarting face detection
            self.face_trackers.clear()
            self.next_face_id = 0
        return self.find_faces

    def get_faces(self) -> None:
        return

    def draw_rect(self, rect: List[int], col: Tuple[int, int, int] = (0, 255, 0), thickness: int = 2) -> None:
        x, y, w, h = rect
        cv2.rectangle(self.frame_out, (x, y), (x + w, y + h), col, thickness)
    
    def match_faces(self, detected_faces: List[List[int]]) -> Dict[int, List[int]]:
        """Match detected faces to existing trackers"""
        matches: Dict[int, List[int]] = {}
        used_tracker_ids = set()
        used_detection_indices = set()
        
        # First pass: match faces that are close to existing trackers
        for tracker_id, tracker in self.face_trackers.items():
            best_match_idx = -1
            best_distance = float('inf')
            
            for idx, face_rect in enumerate(detected_faces):
                if idx in used_detection_indices:
                    continue
                distance = tracker.calculate_distance(face_rect)
                if distance < best_distance and distance < self.max_face_distance:
                    best_distance = distance
                    best_match_idx = idx
            
            if best_match_idx >= 0:
                matches[tracker_id] = detected_faces[best_match_idx]
                used_tracker_ids.add(tracker_id)
                used_detection_indices.add(best_match_idx)
        
        # Second pass: create new trackers for unmatched faces
        for idx, face_rect in enumerate(detected_faces):
            if idx not in used_detection_indices:
                tracker_id = self.next_face_id
                self.next_face_id += 1
                matches[tracker_id] = face_rect
        
        return matches

    def train(self) -> bool:
        self.trained = not self.trained
        return self.trained

    def plot(self) -> None:
        data = np.array(self.data_buffer).T
        np.savetxt("data.dat", data)
        np.savetxt("times.dat", self.times)
        freqs = 60. * self.freqs
        idx = np.where((freqs > 50) & (freqs < 180))
        pylab.figure()
        n = data.shape[0]
        for k in range(n):
            pylab.subplot(n, 1, k + 1)
            pylab.plot(self.times, data[k])
        pylab.savefig("data.png")
        pylab.figure()
        for k in range(self.output_dim):
            pylab.subplot(self.output_dim, 1, k + 1)
            pylab.plot(self.times, self.pcadata[k])
        pylab.savefig("data_pca.png")

        pylab.figure()
        for k in range(self.output_dim):
            pylab.subplot(self.output_dim, 1, k + 1)
            pylab.plot(freqs[idx], self.fft[k][idx])
        pylab.savefig("data_fft.png")
        quit()

    def run(self, cam: int) -> None:
        current_time = time.time() - self.t0
        self.frame_out = self.frame_in.copy()
        self.gray = cv2.equalizeHist(cv2.cvtColor(self.frame_in,
                                                  cv2.COLOR_BGR2GRAY))

        # Helper function to draw text with outline
        def draw_text_with_outline(img, text, pos, font, scale, text_color, outline_color, text_thickness=1, outline_thickness=3, line_type=cv2.LINE_AA):
            x, y = pos
            # Draw outline by drawing text multiple times with offset
            cv2.putText(img, text, (x - 1, y - 1), font, scale, outline_color, outline_thickness, line_type)
            cv2.putText(img, text, (x + 1, y - 1), font, scale, outline_color, outline_thickness, line_type)
            cv2.putText(img, text, (x - 1, y + 1), font, scale, outline_color, outline_thickness, line_type)
            cv2.putText(img, text, (x + 1, y + 1), font, scale, outline_color, outline_thickness, line_type)
            # Draw the main text on top
            cv2.putText(img, text, (x, y), font, scale, text_color, text_thickness, line_type)

        text_color = (255, 255, 255) # White
        outline_color = (0, 0, 0) # Black
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale_controls = 0.6
        font_scale_status = 0.7
        font_scale_bpm = 0.6
        text_thickness = 1
        outline_thickness = 2

        # Detect faces
        detected_faces = list(self.face_cascade.detectMultiScale(self.gray,
                                                               scaleFactor=1.3,
                                                               minNeighbors=4,
                                                               minSize=(50, 50),
                                                               flags=cv2.CASCADE_SCALE_IMAGE))

        if self.find_faces:
            # Face detection mode - show all detected faces
            draw_text_with_outline(
                self.frame_out, f"Press 'C' to change camera (current: {cam})",
                (10, 30), font, font_scale_controls, text_color, outline_color, text_thickness, outline_thickness)
            draw_text_with_outline(
                self.frame_out, "Press 'S' to lock faces and begin tracking",
                (10, 55), font, font_scale_controls, text_color, outline_color, text_thickness, outline_thickness)
            draw_text_with_outline(
                self.frame_out, "Press 'Esc' to quit",
                (10, 80), font, font_scale_controls, text_color, outline_color, text_thickness, outline_thickness)
            
            # Draw all detected faces
            for face_rect in detected_faces:
                x, y, w, h = face_rect
                self.draw_rect(face_rect, col=(255, 0, 0), thickness=2)
                # Draw forehead region preview
                forehead = [int(x + w * 0.5 - (w * 0.25 / 2.0)),
                           int(y + h * 0.18 - (h * 0.15 / 2.0)),
                           int(w * 0.25),
                           int(h * 0.15)]
                self.draw_rect(forehead, col=(0, 255, 0), thickness=1)
            
            # Reset trackers when in face detection mode
            self.face_trackers.clear()
            self.next_face_id = 0
            return

        # Face tracking mode - process all detected faces
        if len(detected_faces) == 0:
            # No faces detected, remove old trackers that haven't been seen
            current_time_abs = time.time()
            trackers_to_remove = []
            for tracker_id, tracker in self.face_trackers.items():
                if current_time_abs - tracker.last_update > self.face_timeout:
                    trackers_to_remove.append(tracker_id)
            for tracker_id in trackers_to_remove:
                del self.face_trackers[tracker_id]
        else:
            # Match detected faces to existing trackers or create new ones
            matches = self.match_faces(detected_faces)
            
            # Update existing trackers and create new ones
            for tracker_id, face_rect in matches.items():
                if tracker_id in self.face_trackers:
                    # Update existing tracker
                    self.face_trackers[tracker_id].update_face_rect(face_rect)
                else:
                    # Create new tracker
                    self.face_trackers[tracker_id] = FaceTracker(tracker_id, face_rect, self.buffer_size)
            
            # Remove trackers that weren't matched
            current_time_abs = time.time()
            trackers_to_remove = []
            for tracker_id in self.face_trackers.keys():
                if tracker_id not in matches:
                    if current_time_abs - self.face_trackers[tracker_id].last_update > self.face_timeout:
                        trackers_to_remove.append(tracker_id)
            for tracker_id in trackers_to_remove:
                del self.face_trackers[tracker_id]

        # Draw controls text when faces are locked
        draw_text_with_outline(
            self.frame_out, f"Press 'C' to change camera (current: {cam})",
            (10, 30), font, font_scale_controls, text_color, outline_color, text_thickness, outline_thickness)
        draw_text_with_outline(
            self.frame_out, "Press 'S' to restart",
            (10, 55), font, font_scale_controls, text_color, outline_color, text_thickness, outline_thickness)
        draw_text_with_outline(
            self.frame_out, "Press 'D' to toggle data plot",
            (10, 80), font, font_scale_controls, text_color, outline_color, text_thickness, outline_thickness)
        draw_text_with_outline(
            self.frame_out, "Press 'Esc' to quit",
            (10, 105), font, font_scale_controls, text_color, outline_color, text_thickness, outline_thickness)
        
        # Show number of tracked faces
        num_faces = len(self.face_trackers)
        draw_text_with_outline(
            self.frame_out, f"Tracking {num_faces} face(s)",
            (10, 130), font, font_scale_controls, text_color, outline_color, text_thickness, outline_thickness)

        # Process each tracked face
        for tracker_id, tracker in self.face_trackers.items():
            # Process frame for this face
            tracker.process_frame(self.frame_in, self.gray, current_time)
            
            # Draw face rectangle
            x, y, w, h = tracker.face_rect
            self.draw_rect(tracker.face_rect, col=tracker.color, thickness=2)
            
            # Draw forehead region
            forehead = tracker.get_subface_coord(0.5, 0.18, 0.25, 0.15)
            self.draw_rect(forehead, col=(0, 255, 0), thickness=1)
            
            # Draw BPM text above face
            if tracker.bpm > 0:
                bpm_text = f"Face {tracker_id + 1}: {tracker.bpm:.1f} BPM"
            else:
                L = len(tracker.data_buffer)
                if L > 10:
                    gap = (tracker.buffer_size - L) / tracker.fps if tracker.fps > 0 else 0
                    bpm_text = f"Face {tracker_id + 1}: Calculating... (wait {gap:.0f}s)"
                else:
                    bpm_text = f"Face {tracker_id + 1}: Initializing..."
            
            # Position text above face rectangle
            text_x = x
            text_y = max(20, y - 10)
            
            draw_text_with_outline(
                self.frame_out, bpm_text,
                (text_x, text_y), font, font_scale_bpm, tracker.color, outline_color, text_thickness, outline_thickness)
        
        # Update backward compatibility attributes (use first face's data)
        if len(self.face_trackers) > 0:
            first_tracker = list(self.face_trackers.values())[0]
            self.bpm = first_tracker.bpm
            self.samples = first_tracker.samples
            self.freqs = first_tracker.freqs
            self.fft = first_tracker.fft
            if len(first_tracker.samples) > 0:
                self.slices = [np.copy(self.frame_out[first_tracker.face_rect[1]:first_tracker.face_rect[1] + first_tracker.face_rect[3],
                                      first_tracker.face_rect[0]:first_tracker.face_rect[0] + first_tracker.face_rect[2], 1])]
        else:
            self.bpm = 0
            self.samples = []
            self.freqs = np.array([])
            self.fft = np.array([])
