import numpy as np
from chaos_nightmare.views.core import View
from PIL import Image
from dataclasses import dataclass
from chaos_nightmare.util.logging_config import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ViewPlacement:
    view: View
    x_pos: int
    y_pos: int
    enabled: bool


class ViewContainer(View):
    views: list[ViewPlacement] = []

    def add_view(self, view: View, x_pos: int, y_pos: int, enabled: bool = True):
        """Add a view to the container"""

        self.views.append(
            ViewPlacement(view=view, x_pos=x_pos, y_pos=y_pos, enabled=enabled)
        )

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
