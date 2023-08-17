from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="chaos_nightmare_")
    access_token: str #twitch access token
    target_fps: float = 0.1 
    image_height: int = 1024
    image_width: int = 1024
    base_sd_url: str = "http://localhost:7860"
    image_gen_rate_seconds: int = 120
    reset_rate: int = 60 * 10
    iteration_thresh: int = 5
    stream_progress: bool = False
    safe_image_dir: str = "./safe_images"
    loading_image_dir: str = "./loading_images"
    error_image_dir: str = "./error_images"
    random_prompt_file: str = "./random_prompts.json"
    gpt_prompt_file: str = "./gpt_prompts.json"
    chat_key: str | None = None


config = Config()
