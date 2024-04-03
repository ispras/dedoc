from typing import Iterable, Optional, Union

import numpy as np


class PerformanceResult:
    """
        This class is used for storing multiple results of measuring some metric (for example, elapsed time)
        with support for calculating mean and std statistics and pretty printing of stored values

        >>> result = PerformanceResult()
        >>> f"result: {result}"  # result: -
        >>> result.add(5.0)
        >>> f"result: {result}"  # result: 5.00
        >>> result.add(8.0)
        >>> f"result: {result}"  # result: 6.50±1.50
        >>> result.mean  # 6.5
        >>> result.std  # 1.5
        >>> partial_result = result / 4
        >>> f"partial_result: {partial_result}"  # partial_result: 1.62±0.38
    """

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
