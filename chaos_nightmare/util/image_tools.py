import numpy as np
import random
from twitchio.ext.routines import Routine, compute_timedelta
from datetime import datetime, timedelta

def is_filtered_image(image:np.ndarray, samples:int =30):
    """
    A very dumb way to check and see if the image has been filtered. Will 
    likely file on very dark images
    """

    w, h, _ = image.shape
    samples = [image[int(random.random()*w)][int(random.random()*h)] for _ in range(samples)]

    return np.average(samples) == 0


if __name__ == "__main__":
    blank_image = np.zeros((1024,1024,3))
    random_image = np.ones((1024,1024,3))*random.random()*255

    assert is_filtered_image(blank_image)
    assert not is_filtered_image(random_image)
