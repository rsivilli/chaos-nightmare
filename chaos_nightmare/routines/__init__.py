from twitchio.ext import routines
from twitchio import Channel
from pyvirtualcam import Camera
from chaos_nightmare.views import ViewContainer
from util import logging
from util.image_tools import is_filtered_image
import random


logger = logging.getLogger(__name__)

@routines.routine(seconds=1)
async def send_frame(cam:Camera, view_container:ViewContainer):
    cam.send(view_container.generate_view())



@routines.routine(minutes=0.5)
async def submit_generation(self):
    if len(self.connected_channels) < 1:
        logger.error("We are not currently connected to any channels!")
        return

    channel: Channel = self.connected_channels[0]

    if self.generating_image:
        logger.info(
            "Looks like we're still generating an image. Skipping this call"
        )
        return
    if len(self.positive_prompt) < 4:
        logger.info("Current Prompt is less than 4 characters. Going to skip")
        tmp = random.choice(self.random_prompts)
        self.positive_prompt_options.add(tmp)
        self.positive_prompt = tmp
        await channel.send(
            f"Looks like we're having trouble thinking of something. A random prompt has been generated to start us off"
        )

    # We're assuming this is only for one channel

    # await channel.send(f"We're now submitting {self.iteration_counter} for image generation. All additional prompts will be used for the next generation unless this is the last generation")

    logger.info("Submitting for image generation")
    self.generating_image = True
    self.check_progress.start(stop_on_error=False)
    self.iteration_counter += 1
    if len(self.last_image) > 0:
        response = await self.sd_client.img2img(
            prompt=self.positive_prompt,
            negative_prompt=self.always_negative + self.negative_prompt,
            input_image=self.last_image,
        )
    else:
        response = await self.sd_client.txt2img(
            prompt=self.positive_prompt,
            negative_prompt=self.always_negative + self.negative_prompt,
        )
    logger.debug("Image received")
    if len(response.images) > 0 and not self.interrupted:
        # For now, let's assume we're only generating one so far
        self.last_image = response.images[0]
        frame = self.sd_client._decode_image(response.images[0])
        logger.debug("Done with decoding image")

        if is_filtered_image(frame):
            logger.info(
                "Filtered image detected. Injecting safe image and resetting"
            )
            frame = self.get_safe_image()
            await self.reset_generation()

            self.main_view.set_image(frame)
            self.history_view.add_frame(frame)

            logger.debug("Done with sending to cam")
        self.generating_image = False

        logger.debug("Done with Image Gen")
        self.check_progress.stop()
        self._reset_cooldowns()
        if self.interrupted:
            self.interrupted = False
        elif self.iteration_counter >= self.iteration_thresh:
            await self.reset_generation()

@submit_generation.error
async def submit_generation_on_error(error:Exception):
    logger.error("Error submitting to generation")
    logger.error(error)
    self.check_progress.stop()
    self.main_view.set_image(random.choice(
        self.error_images
    ))
    
