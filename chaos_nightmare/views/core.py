from PIL import Image
import numpy as np


class View(object):
    image: Image.Image

    def __init__(self, width: int, height: int, color: tuple = (0, 0, 0)) -> None:
        self.image = Image.new("RGB", (width, height), color)

    def clear_view(self):
        self.image.paste((0, 0, 0), (0, 0, self.image.width, self.image.height))

    def generate_view(self) -> np.ndarray:
        return np.array(self.image)


if __name__ == "__main__":
    test = View(1024, 1024)
