from chaos_nightmare.views.core import View
from PIL import Image, ImageDraw, ImageFont
from datetime import timedelta
from chaos_nightmare.util.image_tools import timer_func

class CurrentImageView(View):

    def __init__(self, width: int, height: int, color: tuple[int, int, int] = (0,0,0)) -> None:
        self.raw_image = Image.new("RGB",(width,height),color)
        self.font = ImageFont.truetype("fonts./PressStart2P-Regular.ttf",20)
        super().__init__(width, height, color)
    
    def set_image(self,img:Image.Image):
        self.raw_image = img.resize(
            (self.image.width,self.image.height), resample=Image.Resampling.LANCZOS
        )
    
    def _get_timer_color(self,time_left:timedelta):
        if time_left >timedelta(seconds=30): 
            return (255,255,255)
        if time_left > timedelta(seconds=10):
            return (255,255,77)
        return (255,0,0)
    
    @timer_func
    def update_stats(self, time_till_image_gen:timedelta, iteration_counter:int,iteration_thresh:int, generating_image:bool=False ):
        self.image.paste(self.raw_image)
        d1 = ImageDraw.Draw(self.image)
        w = self.image.width
        h = self.image.height
        
        col_text = f"Time till image collection: {str(time_till_image_gen).split('.')[0]}"
        offset_x = self.font.getlength(col_text)
        d1.text((int(w/2)-int(offset_x/2),10),col_text,fill =self._get_timer_color(time_till_image_gen),font=self.font)
        gen_text = f"Current Image Generation: {iteration_counter} Generations Left: {iteration_thresh-iteration_counter}"
        offset_x = self.font.getlength(gen_text)
        d1.text((int(w/2)-int(offset_x/2),h-20), gen_text,fill=(255,255,255), font=self.font)
        if generating_image:
            gen_text = f"Image generation in Progress!"
            offset_x = self.font.getlength(gen_text)
            d1.text((int(w/2)-int(offset_x/2),int(h/2)), gen_text,fill=(255,255,255), font=self.font)


if __name__ == "__main__":
    tmp = CurrentImageView(1024,1024)
    print(tmp)