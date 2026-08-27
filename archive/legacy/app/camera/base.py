"""Base Frame Source Interface."""
import abc
from typing import Tuple, Optional
import numpy as np

class BaseFrameSource(abc.ABC):
    def __init__(self, config: dict):
        self.config = config
        self.is_opened = False
        self.frame_count = 0

    @abc.abstractmethod
    def open(self) -> bool:
        pass

    @abc.abstractmethod
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray], float, int]:
        pass

    @abc.abstractmethod
    def close(self):
        pass
