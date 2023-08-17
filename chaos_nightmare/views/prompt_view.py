from chaos_nightmare.views.core import View
from PIL import ImageDraw, ImageFont
import textwrap

from chaos_nightmare.util.image_tools import timer_func
from chaos_nightmare.util.logging_config import logging


from math import ceil, sqrt, floor

logger = logging.getLogger(__name__)


class PromptView(View):
    def _calc_font_size(self, text: str) -> int:
        if len(text) < 1:
            return self.default_font_size
        return int(
            min(
                [
                    self.font.size,
                    sqrt(
                        float(self.image.width - 10)
                        * float(self.image.height - 40)
                        / float(len(text))
                    ),
                ]
            )
        )

    def __init__(
        self,
        width: int,
        height: int,
        color: tuple = (0, 0, 0),
        default_font_size: int = 20,
    ) -> None:
        super().__init__(width, height, "Current Image Prompt", color)
        d1 = ImageDraw.Draw(self.image)
        self.font = ImageFont.truetype(
            "fonts./PressStart2P-Regular.ttf", default_font_size
        )
        self.default_font_size = default_font_size
        self._add_title(font=self.font, img_draw=d1)
        self.draw_top()

    @timer_func
    def update_prompt(self, prompt):
        d1 = ImageDraw.Draw(self.image)
        self.clear_view()
        self._add_title(font=self.font, img_draw=d1)

        font_size = self._calc_font_size(prompt)
        line_width = floor(self.image.width / font_size)
        logger.info(
            f"Font calculated to be {font_size} and line width will be set to {line_width}"
        )

        textwrapped = textwrap.wrap(prompt, width=line_width)
        del self.font
        self.font = ImageFont.truetype("fonts./PressStart2P-Regular.ttf", font_size)
        d1.text((10, 40), "\n".join(textwrapped), font=self.font, fill=(255, 255, 255))
        self.draw_top()


if __name__ == "__main__":
    view = PromptView(2560, 416)
    view.update_prompt(
        "In the neon-bathed heart of a sprawling metropolis, where towering monoliths of glass and steel clawed at the smog-choked heavens, a city of paradoxes and disillusionments thrived under the artificial glow of a thousand digital billboards. A hazy veil of synthetic mist clung to the streets, a testament to the unending urban sprawl and the ceaseless churn of industry. The air was heavy with the acrid tang of ozone, the ghostly resonance of countless electronic transactions, and the distant hum of machinery that wove the very fabric of this cybernetic existence. Raindrops, acid raindrops, descended from above, refracting the myriad colors of the luminous advertisements into a kaleidoscope of shimmering hues. Each drop seemed to carry a glimmer of the electronic dreams that this city peddled, fleeting glimpses of a reality that often proved elusive. The streets themselves, paved with a mosaic of circuit-like patterns, echoed with the ceaseless symphony of footsteps, a rhythm of existence inextricably linked to the relentless march of time. Amid this ceaseless chaos, figures cloaked in the shadows of their own augmentations moved with the grace of elusive specters. Neon tattoos pulsed beneath translucent skin, a testament to the intimate fusion of flesh and technology that defined this age. Neon eyes, a myriad of colors and shapes, cast fleeting glances that spoke volumes of veiled secrets and concealed motives. Masks of augmented reality obscured faces, projecting alternate identities onto the canvas of anonymity. Hovering above the labyrinthine streets, airborne vehicles weaved intricate patterns through the air, their wings aflutter with iridescent diodes that mirrored the dazzling skyline below. Neon trails and synthetic halos marked their paths, creating an ethereal ballet against the backdrop of towering edifices. Advertisements and propaganda danced across their sleek surfaces, offering glimpses of perfection, prosperity, and a manufactured reality that could be accessed for the right price. Beneath the relentless sensory bombardment, within the labyrinthine alleyways and hidden corners, a subculture thrived—an underbelly of hackers, rebels, and those who refused to be subjugated by the neon-drenched regime. Their gatherings, cloaked in secrecy and encrypted communications, sparked the flicker of resistance, a defiance against the oppressive regime of megacorporations and techno-authoritarians. In this urban jungle, where the boundary between man and machine blurred, where reality was sculpted by lines of code and virtual currencies held more power than physical coins, a lone figure stood poised at the intersection of despair and possibility. Eyes of circuitry and heart of insurgency, this individual was the embodiment of a digital insurgency, a living testament to the struggle against a world where humanity's connection to its very essence was mediated through screens and implants. As the acid rain pelted the figure's cybernetic skin, it was as if the very elements conspired to wash away the illusions of grandeur, revealing the raw core of a city that thrived on exploitation and control. And in the midst of this tumultuous urban dystopia, the figure's gaze remained unwavering, a beacon of resistance against the electronic tide that sought to drown humanity's essence in the sea of silicon and circuitry."
    )

    view.image.show()
