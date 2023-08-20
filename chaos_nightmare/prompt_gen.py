import openai
from util.image_tools import load_list_file
from config import Config
import random
from dataclasses import dataclass
from pydantic import BaseModel
import re
from util.logging_config import logging

logger = logging.getLogger(__name__)


class PromptGenerator(object):
    random_prompts: list[str] = []
    gpt_prompts: list[str] = []
    api_key_provided:bool = False
    gpt_prompt_file:str =None
    def __init__(self,config: Config = Config()) -> None:
        self.random_prompts = load_list_file(config.random_prompt_file)
        self.gpt_prompts = load_list_file(config.gpt_prompt_file)
        self.gpt_prompt_file = config.gpt_prompt_file
        if config.chat_key is not None:
            openai.api_key = config.chat_key
            self.api_key_provided = True
    def _clean_gpt_response(self,response_content:str)->str:
        return re.sub(r"[^\w\s,.-]","",response_content)
    async def get_random_prompt(self)->str:
        if self.api_key_provided:
            try:
                if len(self.gpt_prompts) == 0:
                    self.gpt_prompts = load_list_file(self.gpt_prompt_file)
                gpt_msg = self.gpt_prompts.pop(random.randint(0,len(self.gpt_prompts)-1))
                logger.info("Sending prompt to chatgpt: "+gpt_msg)
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

    print(prompt_generator._clean_gpt_response(
      "In the vast expanse of the uncharted câ€™osmos, amidst a tapestry of glittering stars, a celestial ballet of lâ€™ight and darkness unfolded, merging with the fabric of time itself. The universe, an enigmatic and limitless canvas, awaited the first brushstrokes of a grand narrative. The setting was an unexplored planet, far-flung from the confines of human knowledge, cloaked in mist and swirling nebulae. The celestial body, christened Nova Terra by astronomers, spanned the horizon with awe-inspiring majesty.  As the pulses of stardust merged and intertwined, the planetâ€™s two suns cast a dualistic glow upon the land, painting everything in hues of ethereal golden and radiant crimson. The air was charged, humming with a magnetic energy, as if the universe was poised on the precipice of great transformation. Gently stirring winds whispered secrets into the ears of the verdant foliage, their rustling leaves a chorus of anticipation. The skies above, adorned with swirling clouds of electric blue and purple, seemed to crackle with hidden power and woven constellations.  At the edge of a dense, enchanted forest, guarded by towering trees, a metallic sheen caught the ever-shifting sunlight, hinting at something extraordinary hidden within its depths. A colossal spaceship, its sleek contours and iridescent silver hull blending seamlessly with the natural surroundings, rested like a slumbering titan. It was a marvel of engineering, a silent sentinel from distant worlds, reflecting the evolutionary wonders that awaited the courageous souls who would dare to traverse the stars.  The spaceship's immense doorway, constructed of luminescent glass, hinted at the mysteries that lay inside. A soft azure light emanated from the core of the vessel, pulsating like a celestial heartbeat. Ponderous, it beckoned the curious, promising the fulfillment of cosmic dreams. The air tingled with an otherworldly electricity, as if the ship itself held both the secrets of past civilizations and the keys to unlocking the future.  Surrounding the spacecraft, a motley crew of intrepid explorers, clad in advanced jumpsuits and equipped with state-of-the-art technology, converged with a sense of both trepidation and determination. Each member carried their own humanity and dreams, an amalgamation of cultures and aspirations from all corners of Earth, united in their quest for enlightenment in the face of the unknown.  With a mechanical hiss, the spacecraft's entryway glided open, revealing a passage of gleaming white corridors, instilling both wonder and fear in equal measure. As the explorers crossed the threshold, their eyes filled with wonder, their hearts throbbing with excitement. Within the bowels of this interstellar titan, they were poised to uncover the secrets of the universe, shaping new destinies with each step, and etching their names in the annals of time as cosmic pioneers.  Thus, the curtains lifted on this intergalactic tale, with Nova Terra's indomitable spirit pulsing as a beacon of exploration, hope, and uncharted wonders beyond imagination."  
    ))
