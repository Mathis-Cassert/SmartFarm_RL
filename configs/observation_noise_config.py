from dataclasses import dataclass
from typing import Literal, Optional, Dict

import numpy as np

from configs.gym_obs_act import ObservationFeature
from utils.seed_utils import get_global_seed


@dataclass
class FeatureNoiseConfig:
    """Noise configuration for a single feature."""
    noise_type: Literal["gaussian", "uniform", "none"] = "gaussian"
    std: float = 0.01
    enabled: bool = True


class NoiseConfig:
    """Configuration for observation noise with named feature mapping."""

    def __init__(
            self,
            enabled: bool = True,
            feature_configs: Optional[Dict[ObservationFeature, FeatureNoiseConfig]] = None,
            seed: Optional[int] = None
    ):
        self.enabled = enabled
        self.feature_configs = feature_configs or {}
        self.seed = seed if seed is not None else get_global_seed()
