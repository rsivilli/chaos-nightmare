from numpy._typing import NDArray
from numpy import uint8
from pydantic import BaseModel
import base64
from PIL import Image
import io
import numpy as np
from aiohttp import ClientSession
from async_timeout import timeout
import asyncio
from chaos_nightmare.util import logging

logger = logging.getLogger(__name__)

base_img2img = {
    "prompt":"",
    "negative_prompt":"BadDream, FastNegativeV2",
    "seed":"-1",
    "cfg_scale":7,
    "sampler_index":"DPM++ 2M Karras",
    "steps":30,
    "denoising_strength":0.7,
    "batch_size":1,
    "width":1024,
    "height":1024,
    "n_iter":1,
    "init_images":[],
    "inpaint_full_res":False,
    "inpainting_fill":1,
    "outpainting_fill":2,
    "enable_hr":False,
    "restore_faces":False,
    "hr_scale":2,
    "hr_upscaler":"None",
    "hr_second_pass_steps":0,
    "hr_resize_x":0,
    "hr_resize_y":0,
    "hr_square_aspect":False,
    "styles":[],
    "upscale_x":2,
    "hr_denoising_strength":0.7,
    "hr_fix_lock_px":0,
    "image_cfg_scale":0.7,
    "save_images": True,
}
base_txt2img = {
    "prompt":"hello world",
    "negative_prompt":"easynegative",
    "seed":"-1",
    "cfg_scale":7,
    "sampler_index":"DPM++ 2M Karras",
    "steps":30,
    "denoising_strength":1,
    "mask_blur":0,
    "batch_size":1,
    "width":1024,
    "height":1024,
    "n_iter":1,
    "mask":"",
    "init_images":[],
    "inpaint_full_res":False,
    "inpainting_fill":1,
    "outpainting_fill":2,
    "enable_hr":False,
    "restore_faces":False,
    "hr_scale":2,
    "hr_upscaler":"None",
    "hr_second_pass_steps":0
    ,"hr_resize_x":0,
    "hr_resize_y":0,
    "hr_square_aspect":False,
    "styles":[],
    "upscale_x":2,
    "hr_denoising_strength":0.7,
    "hr_fix_lock_px":0,
    "alwayson_scripts":{},
    "save_images": True,
    }
class ImageResponse(BaseModel):
    images:list[str] = []
    parameters:dict = {}
    info:str = ""
 

class SDStatusState(BaseModel):
    skipped:bool
    interrupted:bool
    job:str
    job_count:int
    job_timestamp:int
    job_no:int
    sampling_step:int
    sampling_steps:int

class SDStatusResponse(BaseModel):
    progress: float
    eta_relative: float
    state:SDStatusState
    current_image:str|None
    textinfo:str|None
    

class SDClient(object):
    session:ClientSession = None
    async def init_session(self):
        self.session = ClientSession(self.base_url)
    def __init__(self,base_url:str="http://localhost:7860") -> None:
        self.base_url = base_url
        self.loop = asyncio.new_event_loop()
        # future = asyncio.ensure_future(self.init_session(),loop=self.loop)
        # self.loop.run_until_complete(future)
    
    async def _close_session(self):
        if self.session is not None:
            await self.session.close()
    def __del__(self):
       future = asyncio.ensure_future(self._close_session(),loop=self.loop)
       self.loop.run_until_complete(future)
       self.loop.close()
        


    async def txt2img(self,prompt:str="",negative_prompt:str="",uri:str="/sdapi/v1/txt2img")->ImageResponse:
        if self.session is None:
            self.session = ClientSession(self.base_url,trust_env=True)
        base_txt2img["prompt"] = prompt
        base_txt2img["negative_prompt"] = negative_prompt
        async with timeout(300):
            async with self.session.post(uri,json=base_txt2img) as response:
                data = await response.json()

        return ImageResponse(**data)


    async def img2img(self,input_image:str,prompt:str="",negative_prompt:str="",uri:str="/sdapi/v1/img2img",)->ImageResponse:
        if self.session is None:
            self.session = ClientSession(self.base_url,trust_env=True)
        base_img2img["prompt"] = prompt
        base_img2img["negative_prompt"] = negative_prompt
        base_img2img["init_images"] = [input_image]
        async with timeout(300):
            async with self.session.post(uri,json=base_img2img) as response:
                if response.status != 200:
                    logger.error(f"Non 200 status received from SD | message = {response.reason}")
                data = await response.json()
                
        return ImageResponse(**data)

    async def get_progress(self, uri:str="/sdapi/v1/progress",stream_progress:bool=False)->SDStatusResponse:
        if self.session is None:
            self.session = ClientSession(self.base_url,trust_env=True)
        async with timeout(10):
            async with self.session.get(uri,params={"skip_current_image":str(stream_progress).lower()}) as response:
                data = await response.json()
        return SDStatusResponse(**data)


    def _decode_image(self,image_str:str):
        imgdata = base64.b64decode(image_str)
        image = Image.open(io.BytesIO(imgdata))
        return image
                                        
    async def interrupt(self,uri:str = "/sdapi/v1/interrupt"):
        if self.session is None:
            self.session = ClientSession(self.base_url,trust_env=True)
        async with timeout(10):
            async with self.session.post(uri) as response:
                response.raise_for_status()
                data = await response.json()
if __name__ == "__main__":
    client=  SDClient()
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        import datetime
        start_time = datetime.datetime.now()
        response =loop.run_until_complete(client.txt2img(prompt="An alien scene"))
        print(f"Time to receive image {datetime.datetime.now()-start_time}")
        start_time = datetime.datetime.now()
        client._decode_image(response.images[0])
        print(f"Time to decode image {datetime.datetime.now()-start_time}")
        response =loop.run_until_complete(client.img2img(prompt="An alien scene",input_image=response.images[0]))

        
    except KeyboardInterrupt:
        pass
    