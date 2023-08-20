import numpy as np
from chaos_nightmare.views.core import View
from dataclasses import dataclass
from chaos_nightmare.util.logging_config import logging
from datetime import datetime
from PIL import  ImageDraw, ImageFont

logger = logging.getLogger(__name__)


@dataclass
class Contributor:
    name: str
    word_count: int


class ContributorView(View):
    contributors: dict[str, Contributor] = {}

    def __init__(self, width: int, height: int, color: tuple = (0, 0, 0)) -> None:
        self.font = ImageFont.truetype("fonts./PressStart2P-Regular.ttf", 20)
        super().__init__(width, height, "Contributors", color)
        self._add_title(font=self.font)
        self.draw_left()
        self.draw_right()

    def reset(self):
        """Clears the board"""
        self.contributors = {}
        self.clear_view()
        self._add_title(font=self.font)
        self.draw_left()
        self.draw_right()

    def _calc_word_count(self, prompt: str):
        return len(prompt.split(" "))

    def _update_view(self):
        self.clear_view()
        self._add_title(font=self.font)
        tmp: list[Contributor] = [val for val in self.contributors.values()]
        tmp.sort(key=lambda x: x.word_count)
        d1 = ImageDraw.Draw(self.image)
        formated_text = [
            f"{contributor.word_count} {contributor.name}"
            for contributor in tmp[: min([10, len(tmp)])]
        ]
        for i in range(len(formated_text)):
            offset_x =self.font.getlength(formated_text[i])
            d1.text((int(self.image.width / 2 - offset_x / 2), i*self.font.size+50), formated_text[i], font=self.font, fill=(255, 255, 255))
        self.draw_left()
        self.draw_right()

    def add_prompt(self, username, prompt):
        """Add a viewer's contribution to the board"""
        short_name = username[: min(len(username), 10)]
        if self.contributors.get(short_name) is None:
            self.contributors[short_name] = Contributor(
                name=short_name, word_count=self._calc_word_count(prompt)
            )
        else:
            self.contributors[short_name].word_count += self._calc_word_count(prompt)
        self._update_view()

    def generate_view(self) -> np.ndarray:
        # TODO be smarter about this - only redraw what you need to

        logger.debug("Clearing View")
        self.clear_view()
        logger.debug("Done Clearing View")
        for view in self.views:
            start_time = datetime.now()
            if view.enabled:
                self.image.paste(view.view.image, (view.x_pos, view.y_pos))
            logger.debug(f"{type(view.view)} took {datetime.now()-start_time} loading")

        return super().generate_view()


if __name__ == "__main__":
    view = ContributorView(1024, 1024)
    view.image.show()
