"""
Seed management utilities for reproducible experiments.
Sets seeds for all major randomness sources used in the SmartFarm_RL project.
"""

import random
import numpy as np
import torch
import gymnasium

_GLOBAL_SEED: int = 0


def get_global_seed() -> int:
    """
    Get the current global seed that was set by set_all_seeds.

    :return: The global seed, or None if no seed has been set
    """
    return _GLOBAL_SEED


def set_all_seeds(seed: int|None = None,
                  set_cuda_deterministic: bool = True,
                  verbose: int = 0) -> int:
    """
    Set seeds for all randomness sources in the project.

    This function sets seeds for:
    - Python's built-in random module
    - NumPy random number generator
    - PyTorch (CPU and CUDA)
    - Gymnasium environments

    :param seed: Random seed to use. If None, generates a random seed.
    :param set_cuda_deterministic: Whether to set CUDA operations to deterministic.
                                   This may impact performance but ensures reproducibility.
    :param verbose: Whether to print seed information. 0: No output, 1: basic output.

    :return: The actual seed used (useful when seed=None was passed).

    Example:
        >>> # Use a specific seed
        >>> set_all_seeds(42)

        >>> # Use a random seed but know what was chosen
        >>> seed_used = set_all_seeds(None)
        >>> print(f"Random seed used: {seed_used}")
    """
    global _GLOBAL_SEED

    actual_seed: int = seed if seed is not None else random.randint(0, 2 ** 32 - 1)

    # Ensure seed is within valid range
    actual_seed = int(actual_seed) % (2 ** 32)

    # Store globally for access throughout the project
    _GLOBAL_SEED = actual_seed

    if verbose > 0:
        print(f"Setting all seeds to: {actual_seed}")

    # Set Python random seed
    random.seed(actual_seed)

    # Set NumPy random seed
    np.random.seed(actual_seed)

    # Set PyTorch seeds
    torch.manual_seed(actual_seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(actual_seed)
        torch.cuda.manual_seed_all(actual_seed)  # for multi-GPU

        if set_cuda_deterministic:
            # Make CUDA operations deterministic
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
            if verbose > 0:
                print("CUDA deterministic mode enabled (may impact performance)")

    # Set Gymnasium seed for new environments
    # Note: This affects the default seed for newly created environments
    gymnasium.Env.reset.__defaults__ = (actual_seed, None)

    if verbose > 0:
        print("Seeds set for: random, numpy, torch, gymnasium")

    return actual_seed


def get_reset_seed(base_seed: int, reset_id: int = 0) -> int:
    """
    Generate a unique seed for each reset based on a base seed.

    This is useful when creating multiple environments to ensure they have
    different but reproducible random behavior.

    :param base_seed: The base seed used for the overall experiment
    :param reset_id: Unique identifier for this reset

    :return: A seed for this specific reset

    Example:
        >>> seed = set_all_seeds(42)
        >>> reset1_seed = get_reset_seed(seed, 0)  # for first reset
        >>> reset2_seed = get_reset_seed(seed, 1)  # for second reset
    """
    ss = np.random.SeedSequence(base_seed)
    return ss.generate_state(reset_id + 1)[reset_id]


def seed_environment(env, seed: int) -> None:
    """
    Seed a specific environment instance.

    :param env: The environment to seed
    :param seed: The seed to use for this environment
    """
    if hasattr(env, 'reset'):
        # The seed will be applied on the next reset call
        env.seed(seed) if hasattr(env, 'seed') else None
