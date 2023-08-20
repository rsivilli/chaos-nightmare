from twitchio.ext import routines
from twitchio import Channel
from pyvirtualcam import Camera
from chaos_nightmare.views import ViewContainer
from util import logging
from util.image_tools import is_filtered_image
import random


logger = logging.getLogger(__name__)


@routines.routine(seconds=1)
async def send_frame(cam: Camera, view_container: ViewContainer):
    cam.send(view_container.generate_view())


