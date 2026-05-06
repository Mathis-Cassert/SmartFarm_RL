from stable_baselines3.common.callbacks import EvalCallback, CheckpointCallback
from sb3_contrib import RecurrentPPO
from stable_baselines3.common.vec_env import VecEnvWrapper

from configs.model_config import MODEL_CONFIG, TRAINING_CONFIG, CHECKPOINT_CONFIG, EVAL_CONFIG


def train_rppo(env: VecEnvWrapper, eval_env: VecEnvWrapper, verbose: int=1):
    """
    Train a RecurrentPPO model on a given environment.

    :param env: Environment to train on
    :param eval_env: Environment to evaluate on
    :param verbose: Verbosity level 0: no output, 1: basic output, 2: debug output
    :returns: Trained RecurrentPPO model
    """
    # Setup callbacks
    checkpoint_callback = CheckpointCallback(**CHECKPOINT_CONFIG, verbose=verbose)

    eval_callback = EvalCallback(
        eval_env=eval_env,
        **EVAL_CONFIG,
        verbose=verbose
    )

    # Initialize model
    model = RecurrentPPO(**MODEL_CONFIG, env=env, verbose=verbose)

    # Train
    if verbose >= 1 : print("Training model...")
    model.learn(
        total_timesteps=TRAINING_CONFIG["total_timesteps"],
        callback=[checkpoint_callback, eval_callback],
        log_interval=TRAINING_CONFIG["log_interval"],
        progress_bar=True if verbose > 0 else False #FIXME: Progress bar doesn't work on (on pycharm at least)
    )

    return model