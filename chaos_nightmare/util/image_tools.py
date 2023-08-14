import numpy as np
import random
from twitchio.ext.routines import Routine, compute_timedelta
from datetime import datetime, timedelta
from pathlib import Path
from PIL import Image
from json import load
import logging

logger = logging.getLogger(__name__)


def is_filtered_image(image:Image.Image, samples:int =30):
    """
    A very dumb way to check and see if the image has been filtered. Will 
    likely file on very dark images
    """

    samples = [image.getpixel((int(random.random()*image.width),int(random.random()*image.height))) for _ in range(samples)]

    return np.average(samples) == 0

def load_images(dir:str):
    out = []
    files = Path(dir).glob("*.png")

    for f in files:
        image = Image.open(f).convert("RGB")
        out.append(image)
    logger.info(f"{len(out)} images were found and loaded")
    return out

def load_list_file(file:str):
    out = []
    with open(file) as f:
        out = load(f)
    return out


def timer_func(func):

    def wrap_func(*args, **kwargs):
        start_time = datetime.now()
        result = func(*args, **kwargs)
        
        logger.debug(f'Function {func.__name__!r} executed in {(datetime.now() - start_time)}s')
        return result
    return wrap_func

if __name__ == "__main__":
    blank_image = np.zeros((1024,1024,3))
    random_image = np.ones((1024,1024,3))*random.random()*255

    assert is_filtered_image(blank_image)
    assert not is_filtered_image(random_image)
