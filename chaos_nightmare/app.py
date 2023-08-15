from twitchio import Channel, User
from twitchio.ext import commands, routines
from twitchio.ext.commands import Cooldown, Bucket, Command
from twitchio.ext.routines import Routine

from pathlib import Path


from util import logging
from config import Config

import re
from enum import Enum

import pyvirtualcam
import numpy as np
import random

from sd_client import SDClient
from util.image_tools import is_filtered_image, load_images, load_list_file
from constants import HELP_TEXT

from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from json import load
from chaos_nightmare.views import (
    ViewContainer,
    CurrentImageView,
    HistoryView,
    PromptView,
)

logger = logging.getLogger(__name__)


COMMAND_FILTER = r"^[a-zA-Z0-9\s]"


class BOTMODE(str, Enum):
    COLLABORATE = "COLLABORATE"
    COMPETE = "COMPETE"


class Chatbot(commands.Bot):
    mode: BOTMODE = BOTMODE.COLLABORATE
    _positive_prompt: str = ""
    negative_prompt: str = ""
    positive_prompt_options: set[str] = set()
    negative_prompt_options: set[str] = set()
    generating_image: bool = False
    cam: pyvirtualcam.Camera = None
    regsp = re.compile(COMMAND_FILTER)
    sd_client: SDClient
    last_image = ""
    iteration_counter: int = 0
    iteration_thresh = 5
    always_negative = "child, nude, naked, breasts, penis, sex, murder, loli "
    safe_images: list[Image.Image] = []
    loading_images: list[Image.Image] = []
    stream_progress: bool = False
    last_raw_frame: np.ndarray = None
    random_prompts: list[str] = []
    generation_history = []
    interrupted: bool = False

    explain_lookup: dict[str, str] = {}

    def __init__(self, config: Config = Config()):
        self.cam = pyvirtualcam.Camera(
            width=2560, height=1440, fps=config.target_fps, backend="obs"
        )
        logger.info(f"Using virtual camera | {self.cam.device}")
        self.sd_client = SDClient(base_url=config.base_sd_url)
        self.base = np.zeros((self.cam.height, self.cam.width, 3), np.uint8)
        self.iteration_thresh = config.iteration_thresh
        self.stream_progress = config.stream_progress

        self.safe_images = load_images(config.safe_image_dir)
        self.loading_images = load_images(config.loading_image_dir)
        self.random_prompts = load_list_file(config.random_prompt_file)
        self.view_container = ViewContainer(2560, 1440)
        self.main_view = CurrentImageView(1024, 1024)
        self.history_view = HistoryView(1024, 1024)
        self.prompt_view = PromptView(1024, 416)
        self.view_container.add_view(self.main_view, 2560 - 1024, 0)
        self.view_container.add_view(self.history_view, 0, 0)
        self.view_container.add_view(self.prompt_view, 2560 - 1024, 1025)

        super().__init__(
            token=config.access_token,
            initial_channels=["dreamingOfElectricSheep"],
            prefix="!",
        )

    @property
    def positive_prompt(self):
        return self._positive_prompt

    @positive_prompt.setter
    def positive_prompt(self, value):
        self._positive_prompt = value
        self.prompt_view.update_prompt(value)

    @routines.routine(seconds=1)
    async def send_frame(self):
        self.cam.send(self.view_container.generate_view())

    async def reset_generation(self):
        channel: Channel = self.connected_channels[0]
        # await channel.send("That's the last image for this set! Starting everything fresh!")

        self.last_image = ""
        self.positive_prompt = ""
        self.negative_prompt = ""
        self.positive_prompt_options = set()
        self.negative_prompt_options = set()
        self.iteration_counter = 0
        self.generation_history = []

    def _reset_cooldowns(self):
        cooldown: Cooldown
        for cooldown in getattr(self.prompt, "_cooldowns", []):
            logger.debug(f"Resetting cooldown for prompts")
            cooldown.reset()
        for cooldown in getattr(self.negative, "_cooldowns", []):
            logger.debug(f"Resetting cooldown for negative prompts")
            cooldown.reset()

    def get_safe_image(self) -> Image.Image:
        return random.choice(self.safe_images)

    def get_loading_image(self) -> Image.Image:
        return random.choice(self.loading_images)

    @routines.routine(minutes=1)
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

    @routines.routine(seconds=1)
    async def update_metrics(self):
        self.main_view.update_stats(
            generating_image=self.generating_image,
            time_till_image_gen=self.submit_generation.time_till_execution,
            iteration_thresh=self.iteration_thresh,
            iteration_counter=self.iteration_counter,
        )

    @routines.routine(seconds=2)
    async def check_progress(self):
        if not self.generating_image:
            return
        else:
            self.main_view.set_image(self.get_loading_image())

        # logger.info("Checking progress of generation")
        # progress = await self.sd_client.get_progress()
        # if progress.current_image is not None and self.stream_progress:
        #     logger.debug("There's an image in progress!")
        #     frame = self.sd_client._decode_image(progress.current_image)
        #     w,h,d = frame.shape
        #     b_w, b_h, b_d = self.base.shape
        #     diff_w = int((b_w-w)/2)
        #     diff_h = int((b_h-h)/2)
        #     padded_frame = np.pad(frame,((diff_w,diff_w),(diff_h,diff_h),(0,0)),mode="constant",constant_values=0)
        #     #We check just before to make sure we don't stomp on a newly generated image
        #     if self.generating_image:
        #         self.send_frame(padded_frame+self.base)

    @commands.cooldown(rate=1, per=300, bucket=Bucket.member)
    @commands.command()
    async def help(self, ctx: commands.Context):
        await ctx.reply(HELP_TEXT)

    @commands.command()
    async def explain(self, ctx: commands.Context):
        """Explains the requested command. Example !explain list_commands"""
        cmd_name = self._sanitize_command(8, ctx).replace("!", "")
        logger.debug(f"Explain for {cmd_name} called by {ctx.author}")
        cmd: Command = self.commands.get(cmd_name, None)
        if cmd is not None:
            logger.debug(f"Found command {cmd.full_name}")

            await ctx.reply(cmd._callback.__doc__)
        else:
            await ctx.reply(f"I'm sorry, I could not find a command {cmd_name}")

    @commands.cooldown(rate=1, per=300, bucket=Bucket.member)
    @commands.command()
    async def list_commands(self, ctx: commands.Context):
        """Lists all supported commands"""
        out = "The supported commands are as follows: " + ", ".join(
            [f"!{func}" for func in self.commands.keys()]
        )
        await ctx.reply(out)

    async def event_ready(self):
        # Alerting that we are logged in and ready to use commands
        logger.info(f"Logged in as | {self.nick}")
        logger.info(f"User id is | {self.user_id}")

    # @commands.cooldown(rate =1 ,per = 60, bucket=Bucket.member)
    @commands.command()
    async def hello(self, ctx: commands.Context):
        """Hello world sanity check"""
        # Send a hello back!
        await ctx.reply(f"Hello {ctx.author.name}!")

    def _sanitize_command(self, command_length: int, ctx: commands.Context) -> str:
        trimmed_msg = ctx.message.content[command_length:]
        return self.regsp.sub("", trimmed_msg).strip()

    @commands.cooldown(rate=1, per=300, bucket=Bucket.member)
    @commands.command()
    async def start_fresh(self, ctx: commands.Context):
        """Should stop current image generation and reset all values. Ex. !start_fresh"""
        self.interrupted = True
        await self.sd_client.interrupt()
        await self.reset_generation()

        ##TODO add images for interrupted frame
        # frame = np.zeros((self.cam.height, self.cam.width, 3), np.uint8)  # RGB
        # frame[:] = self.cam.frames_sent % 255  # grayscale animation
        # self.send_frame(frame)

        await ctx.reply("Setting the slate clean!")

    @commands.cooldown(rate=5, per=1, bucket=Bucket.member)
    @commands.command()
    async def prompt(self, ctx: commands.Context):
        """Adds a word or phrase to the current prompt for image generation. Ex !prompt a forest"""
        # Update's current prompt with the message

        sanitized_prompt = self._sanitize_command(7, ctx)
        logger.debug(
            f"{ctx.author.name} requesting to add  to prompt. Message | {ctx.message.content}"
        )
        self.positive_prompt_options.add(sanitized_prompt)

        if self.mode == BOTMODE.COLLABORATE:
            self.positive_prompt = ", ".join(self.positive_prompt_options)
        elif self.mode == BOTMODE.COMPETE:
            self.positive_prompt = random.choice(self.positive_prompt_options)
        # await ctx.send(f"Prompt for Generation {self.iteration_counter} is now: {self.positive_prompt}")

    # @commands.cooldown(rate=1,per=300,bucket=Bucket.user)
    # async def event_join(channel: Channel, user:User):
    #     await channel.send(f"Welcome {user.name}! If this is your first time or if it has been a while, you can always use the command !help to get started.")

    @commands.command()
    async def negative(self, ctx: commands.Context):
        """Adds a word or phrase to the current negative prompt. Ex !negative deformed"""
        sanitized_prompt = self._sanitize_command(8, ctx)
        logger.debug(
            f"{ctx.author.name} requesting to add  to negative prompt. Message | {ctx.message.content}"
        )
        self.negative_prompt_options.add(sanitized_prompt)

        if self.mode == BOTMODE.COLLABORATE:
            self.negative_prompt = ", ".join(self.negative_prompt_options)
        elif self.mode == BOTMODE.COMPETE:
            self.negative_prompt = random.choice(self.negative_prompt_options)

        await ctx.send(
            f"Negative Prompt for Generation {self.iteration_counter}: {self.negative_prompt}"
        )

    def __del__(self):
        # In theory, the virtualcam library should do this and this is unneeded
        if getattr(self, "cam", None) is not None:
            self.cam.close()


if __name__ == "__main__":
    config = Config()
    bot = Chatbot(config)
    # bot.update_cam.change_interval(seconds=config.target_fps)
    bot.submit_generation.start(stop_on_error=False)
    bot.update_metrics.start(stop_on_error=False)
    bot.send_frame.start(stop_on_error=False)

    bot.run()
