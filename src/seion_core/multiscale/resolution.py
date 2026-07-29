from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ResolutionLevel:
    resolution: int
    law: object
    projector: object | None = None


@dataclass
class ResolutionFamily:
    levels: list[ResolutionLevel]
    topology: str = "finite-dimensional operator norm"
    uniform_estimates_available: bool = False

    def resolutions(self) -> list[int]:
        return [level.resolution for level in self.levels]

