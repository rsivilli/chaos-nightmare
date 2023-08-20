from twitchio import Channel, User
from twitchio.ext import commands, routines
from twitchio.ext.commands import Cooldown, Bucket, Command
from twitchio.ext.routines import Routine



from util import logging
from config import Config

import re
from enum import Enum

import pyvirtualcam
import numpy as np
import random

from sd_client import SDClient
from util.image_tools import is_filtered_image, load_images
from constants import HELP_TEXT

from PIL import Image

from chaos_nightmare.views import (
    ViewContainer,
    CurrentImageView,
    HistoryView,
    PromptView,
    ContributorView,
)
import asyncio
from chaos_nightmare.routines import send_frame
from chaos_nightmare.prompt_gen import PromptGenerator

logger = logging.getLogger(__name__)


COMMAND_FILTER = r"\W"


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
    always_negative = "child, nude, naked, breasts, penis, sex, murder, loli, logo, copyright, watermark"
    safe_images: list[Image.Image] = []
    loading_images: list[Image.Image] = []
    stream_progress: bool = False
    last_raw_frame: np.ndarray = None
    dreaming: bool = False

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
        self.error_images = load_images(config.error_image_dir)
        self.view_container = ViewContainer(2560, 1440)
        self.main_view = CurrentImageView(1024, 1024)
        self.history_view = HistoryView(1024, 1024, max_size=9)
        self.prompt_view = PromptView(2560, 416)
        self.contributor_view = ContributorView(512, 1024)
        self.view_container.add_view(self.main_view, 2560 - 1024, 0)
        self.view_container.add_view(self.history_view, 0, 0)
        self.view_container.add_view(self.prompt_view, 0, 1025)
        self.view_container.add_view(self.contributor_view, 1025, 0)

        self.prompt_generator = PromptGenerator(config)
        
        self.send_frame:Routine = send_frame
        
        self.send_frame.start(self.cam,self.view_container,stop_on_error=False)
        
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

    async def event_message(self, message):
        if message.echo:
            return
        await self.wake(message.channel)
        if message.content[0] != "!":
            sanitized_msg = self._sanitize_command(message.content)
            self.handle_prompt(sanitized_msg, author_name=message.author.name)
            return
        await self.handle_commands(message)

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
        self.contributor_view.reset()

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

    @routines.routine(minutes=1.5, wait_first=True)
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
        elif len(self.positive_prompt) < 4:
            logger.info("Current Prompt is less than 4 characters. Going to skip")
            tmp = await self.prompt_generator.get_random_prompt()
            self.positive_prompt_options.add(tmp)
            self.positive_prompt = tmp
            if not self.dreaming:
                self.dreaming = True
                await channel.send(
                    f"Looks like folks are taking a break. I'm going to sleep, but send me a message to wake me up"
                )

        # We're assuming this is only for one channel

        # await channel.send(f"We're now submitting {self.iteration_counter} for image generation. All additional prompts will be used for the next generation unless this is the last generation")

        logger.info("Submitting for image generation")
        self.generating_image = True
        try:
            self.check_progress.start(stop_on_error=False)
        except RuntimeError as e:
            logger.warning("Check progress already running and could not start")
            logger.error(e)
        except Exception as e:
            logger.error("Ran into a new error starting check_progress. Check logs")
            logger.error(e)
        self.iteration_counter += 1
        try:
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
        except Exception as error:
            logger.error("Error submitting to generation")
            logger.error(error)
            self.check_progress.stop()
            await asyncio.sleep(0.5)
            self.main_view.set_image(random.choice(self.error_images))

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
            time_till_image_gen=self.submit_generation.next_execution_time,
            iteration_thresh=self.iteration_thresh,
            iteration_counter=self.iteration_counter,
        )
    async def welcome_message(self):
        if len(self.connected_channels) == 0:
            return
        channel: Channel = self.connected_channels[0]
        await channel.send(f"Welcome to the social experiment! If this is your first time or if it has been a while, you can always use the command !help to get started. Otherwise, just throw things into chat and see what the ai creates!")
    
    @routines.routine(seconds=2)
    async def check_progress(self):
        """Quick and dirty routine to cycle loading image"""
        
        # Reminder - originally was used to grab the current generation/preview image from 1111
        # As those images are not automatically filtered, that was proving to be problematic without
        # additional processing 

        if not self.generating_image:
            return
        else:
            self.main_view.set_image(self.get_loading_image())


    @commands.cooldown(rate=1, per=300, bucket=Bucket.member)
    @commands.command()
    async def help(self, ctx: commands.Context):
        await ctx.reply(HELP_TEXT)

    @commands.command()
    async def explain(self, ctx: commands.Context):
        """Explains the requested command. Example !explain list_commands"""
        cmd_name = self._sanitize_command(ctx.message.content, 9).replace("!", "")
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

    def _sanitize_command(self, content: str, command_length: int = None) -> str:
        if command_length is None:
            trimmed_msg = content
        else:
            trimmed_msg = content[command_length:]

        return self.regsp.sub(" ", trimmed_msg).strip()

    @commands.cooldown(rate=1, per=300, bucket=Bucket.member)
    @commands.command()
    async def start_fresh(self, ctx: commands.Context):
        """Should stop current image generation and reset all values. Ex. !start_fresh"""
        
        self.interrupted = True
        await self.sd_client.interrupt()
        await self.reset_generation()

        await ctx.reply("Setting the slate clean!")

    def handle_prompt(self, prompt: str, author_name: str):
        
        self.positive_prompt_options.add(prompt)
        
        if self.mode == BOTMODE.COLLABORATE:
            self.positive_prompt = ", ".join(self.positive_prompt_options)
        elif self.mode == BOTMODE.COMPETE:
            self.positive_prompt = random.choice(self.positive_prompt_options)
        
        self.contributor_view.add_prompt(author_name, prompt)

    async def wake(self, channel: Channel):
        if self.dreaming:
            await channel.send(
                "Sorry, was just dreaming there. Happy to use your ideas too ;-)"
            )
            self.dreaming = False
            await self.sd_client.interrupt()
            await self.reset_generation()

    @commands.cooldown(rate=5, per=1, bucket=Bucket.member)
    @commands.command()
    async def prompt(self, ctx: commands.Context):
        """Adds a word or phrase to the current prompt for image generation. Ex !prompt a forest. 
        It is worth noting that posts to chat without any command accomplish this as well
        """
        # Update's current prompt with the message

        sanitized_prompt = self._sanitize_command(ctx.message.content, 8)
        logger.debug(
            f"{ctx.author.name} requesting to add  to prompt. Message | {ctx.message.content}"
        )
        self.handle_prompt(sanitized_prompt, ctx.author.name)

        # await ctx.send(f"Prompt for Generation {self.iteration_counter} is now: {self.positive_prompt}")


    @commands.command()
    async def negative(self, ctx: commands.Context):
        """Adds a word or phrase to the current negative prompt. Ex !negative deformed"""
        sanitized_prompt = self._sanitize_command(ctx.message.content, 9)
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
    bot.submit_generation.start(stop_on_error=False)
    bot.update_metrics.start(stop_on_error=False)

    bot.run()
