from chaos_nightmare.views.core import View
from PIL import Image, ImageDraw,ImageFont
import textwrap
from datetime import datetime
from chaos_nightmare.util.image_tools import timer_func

class PromptView(View):
    prompt:str
    font = ImageFont.truetype("fonts./PressStart2P-Regular.ttf",20)
    def _add_title(self, img_draw:ImageDraw):
        title = "Current Image Prompt"
        offset_x = self.font.getlength(title)
        img_draw.text((int(self.image.width/2-int(offset_x/2)),10), title,font=self.font, align="center")
    def __init__(self, width: int, height: int, color: tuple = (0,0,0)) -> None:
        super().__init__(width, height, color)
        d1 = ImageDraw.Draw(self.image)
        self._add_title(d1)
    @timer_func
    def update_prompt(self,prompt):
        start = datetime.now() 
        d1 = ImageDraw.Draw(self.image)
        self.clear_view()
        self._add_title(d1)
        textwrapped = textwrap.wrap(prompt, width=50)
        d1.text((10,40), "\n".join(textwrapped),font=self.font,fill=(255,255,255))

if __name__ == "__main__":
    view = PromptView(1024,416)
    view.update_prompt("at dawn, two armies of orcs and men face off before joining battle")

    view.image.show()