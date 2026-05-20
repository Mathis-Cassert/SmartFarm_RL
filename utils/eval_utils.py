import os
import pathlib
import warnings
from functools import partial
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sb3_contrib import RecurrentPPO

from stable_baselines3.common.base_class import BaseAlgorithm
from stable_baselines3.common.vec_env import VecNormalize, DummyVecEnv, VecEnv

from configs.gym_obs_act import OBSERVATION_BOUNDS
from configs.save_config import LOG_DIR, MODEL_DIR
from utils.env_factory import make_gym_env
from utils.observation_process import denormalize_observation


def initiate_eval_model(folder_name: str, use_log: bool = False, step: int = 0, verbose: int = 1)\
        -> tuple[BaseAlgorithm, VecEnv, pathlib.Path, bool]:
    """
    Initiate the evaluation model by loading the environment and model.
    :param folder_name: Path to the folder containing the environment and model files
    :param use_log: If True use the model in the log folder instead of the final model
    :param step: Number of steps of the model to evaluate (-1 for the best model). Only used if use_log is True
    :param verbose: Verbosity level for the environment
    :return: Tuple of the model and the environment
    """
    is_best = True
    if use_log:
        if step > 0:
            checkpoints_dir = LOG_DIR / folder_name / "checkpoints"
            step_pattern = f"_{step}_steps.zip"
            model_files = [f for f in os.listdir(checkpoints_dir) if f.endswith(step_pattern)]
            
            if not model_files:
                warnings.warn(f"No model files for step {step} found in the log folder for {folder_name}. "
                              f"Using the best model instead")
                model_path = LOG_DIR / folder_name / "best_model" / "best_model.zip"
            else:
                model_path = checkpoints_dir / sorted(model_files)[0]
                is_best = False
        elif step == -1:
            model_path = LOG_DIR / folder_name / "best_model" / "best_model.zip"
        else:
            warnings.warn(f"Wrong step number {step} for log model, using the best model instead")
            model_path = LOG_DIR / folder_name / "best_model" / "best_model.zip"
    else:
        model_path = MODEL_DIR / folder_name / "model.zip"

    model_folder: pathlib.Path = model_path.parent
    model_path: str = str(model_path)

    env_path:pathlib.Path = MODEL_DIR / folder_name / "vec_normalize.pkl"

    # Create vectorized environment wrapper (required by Stable Baselines3)
    eval_env = DummyVecEnv([partial(make_gym_env, verbose=verbose)])

    # Load normalization statistics from training to ensure consistent observations
    if os.path.exists(env_path):
        eval_env = VecNormalize.load(str(env_path), eval_env)

    # Configure environment for evaluation (freeze normalization statistics)
    eval_env.training = False
    # Disable reward normalization during evaluation to get true rewards
    eval_env.norm_reward = False

    eval_model = RecurrentPPO.load(model_path, env=eval_env)

    return eval_model, eval_env, model_folder, is_best


def evaluate_model(model: BaseAlgorithm, env: VecEnv)\
        -> tuple[dict[str, list[float]], pd.DataFrame, pd.DataFrame]:
    """
    Evaluates a trained model on a given environment.
    :param model: Trained model to evaluate
    :param env: Environment to evaluate on
    :return: Tuple of history, evaluation output, and evaluation summary
    """
    obs = env.reset()
    lstm_states = None
    episode_starts = np.atleast_1d(True)

    # Get the underlying environment (handles Monitor wrapper)
    base_env = env.envs[0].env if hasattr(env.envs[0], 'env') else env.envs[0]

    # Initialize history dictionary to track metrics throughout the episode
    history = {'lai': [], 'twso': [], 'dvs': [], 'sm': [], 'irrig': [], 'reward': [], 'dates': []}

    dones = False
    # Run simulation until episode terminates
    while not dones:
        # Generate action using model's policy with LSTM state tracking
        # noinspection PyTypeChecker
        action, lstm_states = model.predict(
            obs,
            state=lstm_states,
            episode_start=episode_starts,
            deterministic=True
        )

        # Execute action in environment
        obs, rewards, dones, info = env.step(action)
        episode_starts = np.atleast_1d(dones)

        # Retrieve un-normalized observations for accurate plotting
        # Index [0] extracts single environment from vectorized wrapper
        if isinstance(env, VecNormalize):
            real_obs = env.get_original_obs()[0]
        else:
            real_obs = obs[0]

        real_obs = denormalize_observation(real_obs, OBSERVATION_BOUNDS)

        # Extract crop state variables directly from WOFOST engine
        # TWSO: Total weight of storage organs (grain yield)
        # DVS: Development stage (0=emergence, 1=flowering, 2=maturity)
        # Access the underlying PCSEEnv from Monitor wrapper
        twso = base_env.engine.get_variable("TWSO")
        twso_val = twso if twso is not None else 0.0
        dvs = base_env.engine.get_variable("DVS")
        dvs_val = dvs if dvs is not None else 0.0

        # Record metrics for this timestep
        history['lai'].append(real_obs[0])
        history['twso'].append(twso_val)
        history['dvs'].append(dvs_val)
        history['sm'].append(real_obs[2])
        history['irrig'].append(float(action[0][0]))
        history['reward'].append(rewards[0])

    # Retrieve optimal baseline data from environment for comparison
    eval_output_df, eval_summary_df = base_env.get_eval_outputs()
    eval_output_df = eval_output_df.reset_index(drop=True)
    # Align baseline data length with actual episode length
    eval_output_df = eval_output_df.iloc[:len(history['dvs'])]

    return history, eval_output_df, eval_summary_df

# TODO: Add more information on the graph (e.g. tagp)
def plot_evaluation_results(history: dict[str, list[float]], eval_output_df: pd.DataFrame, folder_path: pathlib.Path,
                            prefix: str = '') -> None:
    """Plot evaluation results comparing model output with optimal baseline.
    :param history: Dict with model results (lai, twso, dvs, sm, irrig, reward keys)
    :param eval_output_df: DataFrame with optimal baseline data (LAI, WSO, DVS, SM columns)
    :param folder_path: Path to the folder where the figure will be saved
    :param prefix: Prefix for the figure filename
    """
    plt.figure(figsize=(10, 12))

    # Subplot 1: Leaf Area Index
    plt.subplot(5, 1, 1)
    plt.plot(eval_output_df['LAI'], label='Optimal (Eval)', color='green', alpha=0.3, linestyle='--')
    plt.plot(history['lai'], label='Model Result', color='green')
    plt.legend()

    # Subplot 2: Grain Yield
    plt.subplot(5, 1, 2)
    plt.plot(eval_output_df['WSO'], label='Optimal (Eval)', color='orange', alpha=0.3, linestyle='--')
    plt.plot(history['twso'], label='Model Result', color='orange')
    plt.legend()

    # Subplot 3: Development Stage
    plt.subplot(5, 1, 3)
    plt.plot(eval_output_df['DVS'], label='Optimal (Eval)', color='brown', alpha=0.3, linestyle='--')
    plt.plot(history['dvs'], label='Model Result', color='brown')
    plt.axhline(y=1.0, color='gray', linestyle='--', alpha=0.5, label='Flowering')
    plt.axhline(y=2.0, color='gray', linestyle='--', alpha=0.5, label='Maturity')
    plt.legend()

    # Subplot 4: Soil Moisture and Irrigation
    plt.subplot(5, 1, 4)
    plt.plot(eval_output_df['SM'], label='Optimal Soil Moisture', color='red', alpha=0.3, linestyle='--')
    plt.bar(range(len(history['irrig'])), history['irrig'], label='Irrigation (cm)', color='blue', alpha=0.5)
    plt.plot(history['sm'], label='Model Soil Moisture', color='red')
    plt.legend()

    # Subplot 5: Reward
    plt.subplot(5, 1, 5)
    plt.plot(history['reward'], label='Reward', color='purple')
    plt.legend()

    plt.tight_layout()
    plt.savefig(folder_path / f"{prefix+'_' if prefix else ''}eval.svg")
    plt.show()

