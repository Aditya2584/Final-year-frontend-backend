
import pytest
import numpy as np
import cv2 # Import cv2 even if not directly used in all tests, as processors.py imports it
from lib.processors import findFaceGetPulse

# Fixture to create a processor instance
@pytest.fixture
def processor():
    """Provides a findFaceGetPulse instance for tests."""
    # Initialize with default parameters
    return findFaceGetPulse()

# Fixture to create a dummy input frame
@pytest.fixture
def dummy_frame():
    """Provides a simple 100x100 BGR image (all gray)."""
    frame = np.full((100, 100, 3), 128, dtype=np.uint8)
    return frame

def test_get_subface_coord(processor):
    """
    Test the calculation of forehead coordinates relative to a face rectangle.
    """
    # Define a sample face rectangle (x, y, w, h)
    processor.face_rect = [10, 10, 50, 50] # Example face at (10,10) with size 50x50

    # Expected forehead coordinates based on default relative values (0.5, 0.18, 0.25, 0.15)
    # x_face = 10, y_face = 10, w_face = 50, h_face = 50
    # fh_x = int(10 + 50*0.5 - (50*0.25 / 2.0)) = int(10 + 25 - 6.25) = int(28.75) = 28
    # fh_y = int(10 + 50*0.18 - (50*0.15 / 2.0)) = int(10 + 9 - 3.75) = int(15.25) = 15
    # fh_w = int(50 * 0.25) = 12
    # fh_h = int(50 * 0.15) = 7
    expected_forehead_rect = [28, 15, 12, 7] # Corrected expected x from 29 to 28

    # Calculate forehead coordinates using the method
    calculated_forehead_rect = processor.get_subface_coord(0.5, 0.18, 0.25, 0.15)

    assert calculated_forehead_rect == expected_forehead_rect

def test_get_subface_means_uniform(processor, dummy_frame):
    """
    Test calculating the mean pixel value within a subface region on a uniform image.
    The mean of all BGR channels should equal the uniform value.
    """
    # Set the dummy frame as the processor's input
    processor.frame_in = dummy_frame
    uniform_value = 128.0 # The value used in dummy_frame

    # Define coordinates for a subface region (e.g., 10x10 area within the 100x100 frame)
    coord = [20, 20, 10, 10] # x, y, w, h

    # Calculate the mean using the method
    mean_val = processor.get_subface_means(coord)

    # The mean of the BGR values in a uniform gray image should be the gray value itself
    assert mean_val == pytest.approx(uniform_value)

def test_find_faces_toggle(processor):
    """
    Test the toggling of the face detection state.
    """
    initial_state = processor.find_faces
    # First toggle
    toggled_state_1 = processor.find_faces_toggle()
    assert toggled_state_1 != initial_state
    assert processor.find_faces == toggled_state_1
    # Second toggle
    toggled_state_2 = processor.find_faces_toggle()
    assert toggled_state_2 == initial_state
    assert processor.find_faces == toggled_state_2

# Note: Testing the full 'run' method is complex due to dependencies on
# face detection results, FFT, timing, etc. It's generally better suited
# for integration testing. These unit tests focus on isolated, deterministic functions.
