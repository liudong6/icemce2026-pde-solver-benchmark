from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Grid2D:
    nx: int
    ny: int
    length_x: float = 1.0
    length_y: float = 1.0

    def __post_init__(self) -> None:
        if self.nx < 3 or self.ny < 3:
            raise ValueError("Grid2D requires at least 3 points in each direction")
        if self.length_x <= 0 or self.length_y <= 0:
            raise ValueError("domain lengths must be positive")

        x1 = np.linspace(0.0, self.length_x, self.nx)
        y1 = np.linspace(0.0, self.length_y, self.ny)
        x, y = np.meshgrid(x1, y1, indexing="ij")
        object.__setattr__(self, "hx", self.length_x / (self.nx - 1))
        object.__setattr__(self, "hy", self.length_y / (self.ny - 1))
        object.__setattr__(self, "x", x)
        object.__setattr__(self, "y", y)
        object.__setattr__(self, "num_interior", (self.nx - 2) * (self.ny - 2))

    def interior_index(self, i: int, j: int) -> int:
        if not (1 <= i <= self.nx - 2 and 1 <= j <= self.ny - 2):
            raise IndexError("interior index out of range")
        return (i - 1) * (self.ny - 2) + (j - 1)

