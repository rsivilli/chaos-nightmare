from chaos_nightmare.views.core import View
from PIL import Image
from math import sqrt, ceil
from chaos_nightmare.util.image_tools import timer_func


class HistoryView(View):
    historical: list[Image.Image] = []

    def __init__(
        self,
        width: int,
        height: int,
        color: tuple[int, int, int] = (0, 0, 0),
        max_size: int = 5,
    ) -> None:
        if max_size <= 0:
            raise ValueError("Max size of the historical queue must be > 0")
        self.max_size = max_size
        super().__init__(width, height, color)

    def _calc_per_side(self):
        "Given current number of images in the queue, calculate how many images per row there should be"
        return ceil(sqrt(len(self.historical)))

    @timer_func
    def add_frame(self, frame: Image.Image = None):
        # Reset Image frame
        self.clear_view()

        # Add new frame to end of list and remove from top to max size
        self.historical.append(frame)
        while len(self.historical) > self.max_size:
            self.historical.pop(0)

        # Calc image size based on number in queue and resize
        num_images_per_row = self._calc_per_side()
        image_width = int(self.image.width / num_images_per_row)
        image_height = int(self.image.height / num_images_per_row)

        resized_images = [
            img.resize((image_width, image_height), resample=Image.Resampling.LANCZOS)
            for img in self.historical
        ]

        j = 0
        while len(resized_images):
            for i in range(num_images_per_row):
                if len(resized_images) > 0:
                    u_0 = i * image_width
                    v_0 = j * image_height
                    self.image.paste(
                        resized_images.pop(),
                        (u_0, v_0, u_0 + image_width, v_0 + image_height),
                    )

            j += 1
