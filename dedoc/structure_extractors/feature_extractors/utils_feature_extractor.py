def normalization_by_min_max(feature_value: float, min_v: float, max_v: float) -> float:
    """
    Simple normalization: ( x-min ) / max - min
    @return: normalized feature with a value of [0;1]
    """
    return 0.0 if (max_v - min_v) == 0.0 else (feature_value - min_v) / (max_v - min_v)
