import openai
from util.image_tools import load_list_file
from config import Config
import random


from util.logging_config import logging

logger = logging.getLogger(__name__)


class PromptGenerator(object):
    random_prompts: list[str] = []
    gpt_prompts: list[str] = []
    api_key_provided: bool = False

    def __init__(self, config: Config = Config()) -> None:
        self.random_prompts = load_list_file(config.random_prompt_file)
        self.gpt_prompts = load_list_file(config.gpt_prompt_file)
        if config.chat_key is not None:
            openai.api_key = config.chat_key
            self.api_key_provided = True

    def _clean_gpt_response(self, response_content: str) -> str:
        return response_content.replace("\n", " ")

    async def get_random_prompt(self) -> str:
        if self.api_key_provided:
            try:
                gpt_msg = random.choice(self.gpt_prompts)
                logger.info("Sending prompt to chatgpt: " + gpt_msg)
                response = await openai.ChatCompletion.acreate(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": gpt_msg}],
                )
                out = self._clean_gpt_response(response.choices[0].message.content)
                logger.info("Response, after cleaning, is: " + out)
                return out
            except Exception as e:
                logger.error("Trouble Reaching out to gpt")
                logger.error(e)

        return random.choice(self.random_prompts)


if __name__ == "__main__":
    prompt_generator = PromptGenerator()

    print(prompt_generator.get_random_prompt())
