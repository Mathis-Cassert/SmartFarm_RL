import pathlib
from datetime import datetime

from stable_baselines3.common.base_class import BaseAlgorithm
from stable_baselines3.common.callbacks import EvalCallback, CheckpointCallback
from sb3_contrib import RecurrentPPO
from stable_baselines3.common.vec_env import VecEnv

from configs.model_config import MODEL_CONFIG, TRAINING_CONFIG, CHECKPOINT_CONFIG, EVAL_CONFIG
from configs.save_config import LOG_DIR


def train_rppo(env: VecEnv, eval_env: VecEnv, time_start: str=None, verbose: int=1) -> BaseAlgorithm:
    """
    Train a RecurrentPPO model on a given environment.

    :param env: Environment to train on
    :param eval_env: Environment to evaluate on
    :param time_start: Start time for logging
    :param verbose: Verbosity level 0: no output, 1: basic output, 2: debug output
    :returns: Trained RecurrentPPO model
    """

    # Initialize model
    model: BaseAlgorithm = RecurrentPPO(**MODEL_CONFIG, env=env, verbose=verbose)

    # Log paths
    if time_start is None:
        time_start = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_folder: pathlib.Path = LOG_DIR / f"{time_start}_{model.__class__.__name__}"

    # Setup callbacks
    checkpoint_callback = CheckpointCallback(
        **CHECKPOINT_CONFIG,
        verbose=verbose,
        save_path=str(log_folder / 'checkpoints')
    )

    eval_callback = EvalCallback(
        eval_env=eval_env,
        **EVAL_CONFIG,
        log_path=str(log_folder / 'eval'),
        best_model_save_path=str(log_folder / 'best_model'),
        verbose=verbose,
    )

    # Train
    if verbose >= 1 : print("Training model...")
    model.learn(
        total_timesteps=TRAINING_CONFIG["total_timesteps"],
        callback=[checkpoint_callback, eval_callback],
        log_interval=TRAINING_CONFIG["log_interval"],
        progress_bar=True if verbose > 0 else False #FIXME: Progress bar doesn't work on (on pycharm at least)
    )

    return model