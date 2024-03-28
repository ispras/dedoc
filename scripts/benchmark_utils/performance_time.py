from typing import Iterable, Optional, Union

import numpy as np


class PerformanceResult:
    def __init__(self, results: Optional[Iterable["PerformanceResult"]] = None) -> None:
        self.values = []

        if results is not None:
            for result in results:
                self.add(result)

    def add(self, value: Union[float, "PerformanceResult"]) -> None:
        if isinstance(value, PerformanceResult):
            self.values.extend(value.values)
        else:
            self.values.append(value)

    @property
    def mean(self) -> float:
        return np.mean(self.values) if self.values else 0

    @property
    def std(self) -> float:
        return np.std(self.values) if self.values else 0

    def __str__(self) -> str:
        if not self.values:
            return "-"

        if len(self.values) == 1:
            return f"{self.mean:.2f}"

        return f"{self.mean:.2f}±{self.std:.2f}"

    def __truediv__(self, scale: float) -> "PerformanceResult":
        result = PerformanceResult()

        for t in self.values:
            result.add(t / scale)

        return result
