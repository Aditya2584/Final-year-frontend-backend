from lib.device import Camera
from lib.processors import findFaceGetPulse # Updated import
from lib.interface import plotXY, imshow, waitKey, destroyWindow
from cv2 import moveWindow
import argparse
import numpy as np
import datetime
# Serial port code removed
import socket
import sys
from typing import Dict, List, Tuple, Optional, Any, Callable, Union

class getPulseApp:
    """
    Python application that finds multiple faces in a webcam stream, then isolates the
    forehead region for each face.

    Then the average green-light intensity in each forehead region is gathered
    over time, and each detected person's pulse is estimated simultaneously.
    """

    def __init__(self, args: argparse.Namespace):
        # Imaging device - must be a connected camera (not an ip camera or mjpeg
        # stream)
        # Serial port code removed
        self.send_udp = False

        # Setup UDP communication if requested
        udp = args.udp
        if udp:
            self.send_udp = True
            if ":" not in udp:
                ip = udp
                port = 5005
            else:
                ip, port = udp.split(":")
                port = int(port)
            self.udp = (ip, port)
            self.sock = socket.socket(socket.AF_INET,  # Internet
                                     socket.SOCK_DGRAM)  # UDP

        # Initialize cameras
        self.cameras: List[Camera] = []
        self.selected_cam = 0
        for i in range(3):
            camera = Camera(camera=i)  # first camera by default
            if camera.valid or not len(self.cameras):
                self.cameras.append(camera)
            else:
                break
                    
        self.w, self.h = 0, 0
        self.pressed = 0
        
        # Initialize the pulse detector processor
        # This is designed to handle all image & signal analysis,
        # such as face detection, forehead isolation, time series collection,
        # heart-beat detection, etc.
        self.processor = findFaceGetPulse(bpm_limits=[50, 160],
                                         data_spike_limit=2500.,
                                         face_detector_smoothness=10.)

        # Init parameters for the cardiac data plot
        self.bpm_plot = False
        self.plot_title = "Data display - raw signal (top) and PSD (bottom)"

        # Maps keystrokes to specified methods
        # (A GUI window must have focus for these to work)
        self.key_controls: Dict[str, Callable] = {
            "s": self.toggle_search,
            "d": self.toggle_display_plot,
            "c": self.toggle_cam,
            "f": self.write_csv
        }

    def toggle_cam(self) -> None:
        """
        Switch to the next available camera.
        """
        if len(self.cameras) > 1:
            self.processor.find_faces = True
            self.bpm_plot = False
            destroyWindow(self.plot_title)
            self.selected_cam += 1
            self.selected_cam = self.selected_cam % len(self.cameras)

    def write_csv(self) -> None:
        """
        Writes current data to csv files for each tracked face.
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        timestamp = timestamp.replace(":", "_").replace(".", "_")
        
        if len(self.processor.face_trackers) == 0:
            print("No faces being tracked. Press 'S' to start tracking.")
            return
        
        for tracker_id, tracker in self.processor.face_trackers.items():
            if len(tracker.times) > 0 and len(tracker.samples) > 0:
                fn = f"Webcam-pulse-Face{tracker_id + 1}-{timestamp}"
                data = np.vstack((tracker.times, tracker.samples)).T
                np.savetxt(f"{fn}.csv", data, delimiter=',')
                print(f"Writing csv for Face {tracker_id + 1}: {fn}.csv")
        
        print(f"CSV files written for {len(self.processor.face_trackers)} face(s)")

    def toggle_search(self) -> None:
        """
        Toggles a motion lock on the processor's face detection component.

        Locking the forehead location in place significantly improves
        data quality, once a forehead has been successfully isolated.
        """
        state = self.processor.find_faces_toggle()
        print(f"face detection lock = {not state}")

    def toggle_display_plot(self) -> None:
        """
        Toggles the data display.
        """
        if self.bpm_plot:
            print("bpm plot disabled")
            self.bpm_plot = False
            destroyWindow(self.plot_title)
        else:
            print("bpm plot enabled")
            if self.processor.find_faces:
                self.toggle_search()
            self.bpm_plot = True
            self.make_bpm_plot()
            # Position plot window near the top-left corner of the screen
            moveWindow(self.plot_title, 10, 10) 

    def make_bpm_plot(self) -> None:
        """
        Creates and/or updates the data display.
        Shows data for the first tracked face (or all faces if multiple plots are needed).
        """
        if len(self.processor.face_trackers) == 0:
            return
        
        # Use first face's data for the plot (backward compatibility)
        first_tracker = list(self.processor.face_trackers.values())[0]
        
        if len(first_tracker.times) > 0 and len(first_tracker.samples) > 0:
            # Get background slice if available
            bg = None
            if len(self.processor.slices) > 0 and self.processor.slices[0] is not None:
                bg = self.processor.slices[0]
            
            plotXY([[first_tracker.times,
                    first_tracker.samples],
                   [first_tracker.freqs,
                    first_tracker.fft]],
                  labels=[False, True],
                  showmax=[False, "bpm"],
                  label_ndigits=[0, 0],
                  showmax_digits=[0, 1],
                  skip=[3, 3],
                  name=self.plot_title,
                  bg=bg)

    def key_handler(self) -> None:
        """
        Handle keystrokes, as set at the bottom of __init__()

        A plotting or camera frame window must have focus for keypresses to be
        detected.
        """
        self.pressed = waitKey(10) & 255  # wait for keypress for 10 ms
        if self.pressed == 27:  # exit program on 'esc'
            print("Exiting")
            for cam in self.cameras:
                cam.cam.release()
            # Serial port code removed
            sys.exit()

        for key in self.key_controls.keys():
            if chr(self.pressed) == key:
                self.key_controls[key]()

    def main_loop(self) -> None:
        """
        Single iteration of the application's main loop.
        """
        # Get current image frame from the camera
        frame = self.cameras[self.selected_cam].get_frame()
        self.h, self.w, _c = frame.shape

        # Set current image frame to the processor's input
        self.processor.frame_in = frame
        # Process the image frame to perform all needed analysis
        self.processor.run(self.selected_cam)
        # Collect the output frame for display
        output_frame = self.processor.frame_out

        # Show the processed/annotated output frame
        imshow("Processed", output_frame)
        # Ensure main window is positioned at top-left (moved after imshow)
        moveWindow("Processed", 0, 0) 

        # Create and/or update the raw data display if needed
        if self.bpm_plot:
            self.make_bpm_plot()

        # Serial port code removed

        # Send data via UDP if enabled
        # Send all BPM values as JSON-like format: "face1:bpm1,face2:bpm2,..."
        if self.send_udp:
            if len(self.processor.face_trackers) > 0:
                bpm_data = ",".join([f"face{tracker_id + 1}:{tracker.bpm:.1f}" 
                                     for tracker_id, tracker in self.processor.face_trackers.items()])
                self.sock.sendto(bpm_data.encode('utf-8'), self.udp)
            else:
                self.sock.sendto("no_faces:0".encode('utf-8'), self.udp)

        # Handle any key presses
        self.key_handler()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Webcam pulse detector.')
    # Serial port arguments removed
    parser.add_argument('--udp', default=None,
                       help='udp address:port destination for bpm data')

    args = parser.parse_args()
    App = getPulseApp(args)
    while True:
        App.main_loop()
