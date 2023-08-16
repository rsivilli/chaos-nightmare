from PIL import Image,ImageDraw,ImageFont, ImageOps
import numpy as np


class View(object):
    image: Image.Image
   

    def __init__(self, width: int, height: int, title:str="", color: tuple = (0, 0, 0)) -> None:
        self.image = Image.new("RGB", (width, height), color)
        self.title:str = title

    def clear_view(self):
        self.image.paste((0, 0, 0), (0, 0, self.image.width, self.image.height))

    def draw_border(self):
        d1 = self.get_draw_image()
        d1.rectangle((1,1,self.image.width-1,self.image.height-1),outline="white")
    def generate_view(self) -> np.ndarray:       
        return np.array(self.image)
    def _add_title(self, font:ImageFont.FreeTypeFont, title:str=None,vertical_buffer:int=10,img_draw: ImageDraw.ImageDraw=None):
        if img_draw is None:
            img_draw = self.get_draw_image()
        if title is None:
            title = self.title
        offset_x =font.getlength(title)
        
        img_draw.text(
            (int(self.image.width / 2 - int(offset_x / 2)), vertical_buffer),
            title,
            font=font,
            align="center",
        )
    def get_draw_image(self)->ImageDraw.ImageDraw:
        
        return ImageDraw.Draw(self.image)
    
    def draw_top(self):
        d1 = self.get_draw_image()
        d1.line([(0,0),(self.image.width,0)],fill="white")
    def draw_bottom(self):
        d1 = self.get_draw_image()
        d1.line([(0,self.image.height-1),(self.image.width,self.image.height-1)],fill="white")
    def draw_left(self):
        d1 = self.get_draw_image()
        d1.line([(0,0),(0,self.image.height)],fill="white")
    def draw_right(self):
        d1 = self.get_draw_image()
        d1.line([(self.image.width-1,0),(self.image.width-1,self.image.height)],fill="white")
if __name__ == "__main__":
    test = View(1024, 1024)
