import warnings
from typing import Dict

import numpy as np

from configs.observation_noise_config import NoiseConfig
from configs.gym_obs_act import ObservationFeature
from utils.seed_utils import get_reset_seed


def dict_to_array(obs_dict: Dict[ObservationFeature, float|int]) -> np.ndarray:
    """
    Converts observation dict to numpy array in Enum order.

    :param obs_dict: Dictionary with ObservationFeature keys
    :returns: Numpy array in the order defined by ObservationFeature Enum
    """
    # Sort by Enum value to ensure consistent order
    sorted_features = sorted(obs_dict.keys(), key=lambda x: x.value)
    return np.array([obs_dict[f] for f in sorted_features], dtype=np.float32)

#TODO: Return the same type for the output than the input (float or int)
#TODO: Add noise type that scale with the value of the observation
def apply_noise(
        observation: Dict[ObservationFeature, float | int],
        config: NoiseConfig,
        observation_bounds: Dict[ObservationFeature, tuple[float, float]],
        reset_count: int = 0
) -> np.ndarray:
    """
    Applies per-feature noise to observations.

    :param observation: A dict with ObservationFeature keys
    :param config: NoiseConfig instance
    :param observation_bounds: Dict of (low, high) bounds for each feature
    :param reset_count: Current reset counter for varying noise across resets

    :returns: Noisy observation as numpy array (clipped to valid range)
    """
    obs_array = dict_to_array(observation)

    # Convert bounds dict to arrays
    obs_low = np.array([observation_bounds[f][0] for f in ObservationFeature], dtype=np.float32)
    obs_high = np.array([observation_bounds[f][1] for f in ObservationFeature], dtype=np.float32)

    if not config.enabled:
        return obs_array

    noisy_obs = obs_array.copy()

    # Create a local random generator with varying seed based on reset count
    if config.seed is not None:
        # Combine base seed with reset count for varying but reproducible noise
        noise_seed = get_reset_seed(config.seed, reset_count)
        rng = np.random.RandomState(noise_seed)
    else:
        rng = np.random

    for feature, feature_config in config.feature_configs.items():
        idx = feature.value

        if idx >= len(noisy_obs):
            continue

        if not feature_config.enabled or feature_config.noise_type == "none":
            continue

        if feature_config.noise_type == "gaussian":
            noise = rng.normal(0, feature_config.std)
        elif feature_config.noise_type == "uniform":
            noise = rng.uniform(-feature_config.std, feature_config.std)
        else:
            warnings.warn(f"Unknown/Unsupported noise type: {feature_config.noise_type}")
            continue

        noisy_obs[idx] += noise

    return np.clip(noisy_obs, obs_low, obs_high)

def normalize_observation(observation: np.ndarray,
                          observation_bounds: Dict[ObservationFeature, tuple[float, float]]) -> np.ndarray:
    """
    Normalizes an observation array to the [0, 1] range.
    :param observation: A numpy array of observations
    :param observation_bounds: Dict of (low, high) bounds for each feature
    :returns: Normalized observation as numpy array
    """
    obs_low = np.array([observation_bounds[f][0] for f in ObservationFeature], dtype=np.float32)
    obs_high = np.array([observation_bounds[f][1] for f in ObservationFeature], dtype=np.float32)
    return (observation - obs_low) / (obs_high - obs_low)

def denormalize_observation(observation: np.ndarray,
                          observation_bounds: Dict[ObservationFeature, tuple[float, float]]) -> np.ndarray:
    """
    De-normalizes an observation array from the [0, 1] range to the original range.
    :param observation: A numpy array of observations
    :param observation_bounds: Dict of (low, high) bounds for each feature
    :returns: De-normalized observation as numpy array
    """
    obs_low = np.array([observation_bounds[f][0] for f in ObservationFeature], dtype=np.float32)
    obs_high = np.array([observation_bounds[f][1] for f in ObservationFeature], dtype=np.float32)
    return observation * (obs_high - obs_low) + obs_low