import cv2
import time
import numpy as np
from typing import List, Tuple, Optional, Any, Union, Callable

"""
Wraps up some interfaces to opencv user interface methods (displaying
image frames, event handling, etc).

If desired, an alternative UI could be built and imported into get_pulse.py 
instead. Opencv is used to perform much of the data analysis, but there is no
reason it has to be used to handle the UI as well. It just happens to be very
effective for our purposes.
"""

def resize(*args: Any, **kwargs: Any) -> np.ndarray:
    """Wrapper for cv2.resize"""
    return cv2.resize(*args, **kwargs)


def moveWindow(*args: Any, **kwargs: Any) -> None:
    """Wrapper for cv2.moveWindow"""
    return


def imshow(*args: Any, **kwargs: Any) -> None:
    """Wrapper for cv2.imshow"""
    return cv2.imshow(*args, **kwargs)
    

def destroyWindow(*args: Any, **kwargs: Any) -> None:
    """Wrapper for cv2.destroyWindow"""
    return cv2.destroyWindow(*args, **kwargs)


def waitKey(*args: Any, **kwargs: Any) -> int:
    """Wrapper for cv2.waitKey"""
    return cv2.waitKey(*args, **kwargs)


"""
The rest of this file defines some GUI plotting functionality. There are plenty
of other ways to do simple x-y data plots in python, but this application uses 
cv2.imshow to do real-time data plotting and handle user interaction.

This is entirely independent of the data calculation functions, so it can be 
replaced in the get_pulse.py application easily.
"""


def combine(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    """
    Stack images horizontally.
    
    Args:
        left: Left image
        right: Right image
        
    Returns:
        Combined image
    """
    h = max(left.shape[0], right.shape[0])
    w = left.shape[1] + right.shape[1]
    
    shape = list(left.shape)
    shape[0] = h
    shape[1] = w
    
    comb = np.zeros(tuple(shape), left.dtype)
    
    # left will be on left, aligned top, with right on right
    comb[:left.shape[0], :left.shape[1]] = left
    comb[:right.shape[0], left.shape[1]:] = right
    
    return comb   


def plotXY(data: List[Tuple[List, List]], 
           size: Tuple[int, int] = (280, 640),
           margin: int = 25,
           name: str = "data",
           labels: List[bool] = None, 
           skip: List[int] = None,
           showmax: List[bool] = None, 
           bg: Optional[np.ndarray] = None,
           label_ndigits: List[int] = None, 
           showmax_digits: List[int] = None) -> None:
    """
    Plot XY data on an image and display it using OpenCV.
    
    Args:
        data: List of (x, y) data pairs to plot
        size: Size of the output image (height, width)
        margin: Margin around the plots
        name: Window name for display
        labels: List of booleans indicating whether to show labels for each plot
        skip: List of integers indicating how many points to skip when labeling
        showmax: List of booleans indicating whether to show max value for each plot
        bg: Optional background image
        label_ndigits: List of integers indicating number of decimal places for labels
        showmax_digits: List of integers indicating number of decimal places for max values
    """
    # Initialize default values for optional parameters
    if labels is None:
        labels = []
    if skip is None:
        skip = []
    if showmax is None:
        showmax = []
    if label_ndigits is None:
        label_ndigits = []
    if showmax_digits is None:
        showmax_digits = []
    
    # Validate data
    for x, y in data:
        if len(x) < 2 or len(y) < 2:
            return
    
    n_plots = len(data)
    w = float(size[1])
    h = size[0] / float(n_plots)
    
    z = np.zeros((size[0], size[1], 3))
    
    # Handle background image if provided
    if isinstance(bg, np.ndarray):
        wd = int(bg.shape[1] / bg.shape[0] * h)
        bg = cv2.resize(bg, (wd, int(h)))
        if len(bg.shape) == 3:
            r = combine(bg[:, :, 0], z[:, :, 0])
            g = combine(bg[:, :, 1], z[:, :, 1])
            b = combine(bg[:, :, 2], z[:, :, 2])
        else:
            r = combine(bg, z[:, :, 0])
            g = combine(bg, z[:, :, 1])
            b = combine(bg, z[:, :, 2])
        z = cv2.merge([r, g, b])[:, :-wd, ]    
    
    i = 0
    P = []
    for x, y in data:
        x = np.array(x)
        y = -np.array(y)
        
        # Scale data to fit in the plot area
        xx = (w - 2 * margin) * (x - x.min()) / (x.max() - x.min()) + margin
        yy = (h - 2 * margin) * (y - y.min()) / (y.max() - y.min()) + margin + i * h
        
        # Add labels if requested
        if labels and i < len(labels) and labels[i]:
            for ii in range(len(x)):
                if ii % skip[i] == 0:
                    col = (255, 255, 255)
                    ss = f'{{0:.{label_ndigits[i]}f}}'
                    ss = ss.format(x[ii]) 
                    cv2.putText(z, ss, (int(xx[ii]), int((i+1)*h)),
                                cv2.FONT_HERSHEY_PLAIN, 1, col)           
        
        # Show max value if requested
        if showmax and i < len(showmax) and showmax[i]:
            col = (0, 255, 0)    
            ii = np.argmax(-y)
            ss = f'{{0:.{showmax_digits[i]}f}} {showmax[i]}'
            ss = ss.format(x[ii]) 
            cv2.putText(z, ss, (int(xx[ii]), int((yy[ii]))),
                        cv2.FONT_HERSHEY_PLAIN, 2, col)
        
        try:
            pts = np.array([[int(x_), int(y_)] for x_, y_ in zip(xx, yy)], np.int32)
            i += 1
            P.append(pts)
        except ValueError:
            pass  # temporary
    
    """ 
    # Polylines seems to have some trouble rendering multiple polys for some people
    for p in P:
        cv2.polylines(z, [p], False, (255, 255, 255), 1)
    """
    
    # Hack-y alternative to draw lines between points
    for p in P:
        for i in range(len(p) - 1):
            cv2.line(z, tuple(p[i]), tuple(p[i+1]), (255, 255, 255), 1)    
    
    cv2.imshow(name, z)
