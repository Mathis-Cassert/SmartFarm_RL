from functools import partial
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sb3_contrib import RecurrentPPO

from stable_baselines3.common.base_class import BaseAlgorithm
from stable_baselines3.common.vec_env import VecNormalize, DummyVecEnv

from utils.env_factory import make_gym_env

def initiate_eval_model(folder_path: str, verbose: int = 1) -> tuple[BaseAlgorithm, VecNormalize]:
    """
    Initiate the evaluation model by loading the environment and model.
    :param folder_path: Path to the folder containing the environment and model files
    :param verbose: Verbosity level for the environment
    :return: Tuple of the model and the environment
    """
    env_path = folder_path + "/vec_normalize.pkl"
    model_path = folder_path + "/model.zip"

    # Create vectorized environment wrapper (required by Stable Baselines3)
    eval_env = DummyVecEnv([partial(make_gym_env, verbose=verbose)])

    # Load normalization statistics from training to ensure consistent observations
    eval_env = VecNormalize.load(env_path, eval_env)

    # Configure environment for evaluation (freeze normalization statistics)
    eval_env.training = False
    # Disable reward normalization during evaluation to get true rewards
    eval_env.norm_reward = False

    eval_model = RecurrentPPO.load(model_path, env=eval_env)

    return eval_model, eval_env


def evaluate_model(model: BaseAlgorithm, env: VecNormalize)\
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
        real_obs = env.get_original_obs()[0]

        # Extract crop state variables directly from WOFOST engine
        # TWSO: Total weight of storage organs (grain yield)
        # DVS: Development stage (0=emergence, 1=flowering, 2=maturity)
        twso = env.envs[0].engine.get_variable("TWSO")
        twso_val = twso if twso is not None else 0.0
        dvs = env.envs[0].engine.get_variable("DVS")
        dvs_val = dvs if dvs is not None else 0.0

        # Record metrics for this timestep
        history['lai'].append(real_obs[0])
        history['twso'].append(twso_val)
        history['dvs'].append(dvs_val)
        history['sm'].append(real_obs[2])
        history['irrig'].append(float(action[0][0]))
        history['reward'].append(rewards[0])

    # Retrieve optimal baseline data from environment for comparison
    eval_output_df, eval_summary_df = env.envs[0].get_eval_outputs()
    eval_output_df = eval_output_df.reset_index(drop=True)
    # Align baseline data length with actual episode length
    eval_output_df = eval_output_df.iloc[:len(history['dvs'])]

    return history, eval_output_df, eval_summary_df


def plot_evaluation_results(history: dict[str, list[float]], eval_output_df: pd.DataFrame):
    """Plot evaluation results comparing model output with optimal baseline.
    :param history: Dict with model results (lai, twso, dvs, sm, irrig, reward keys)
    :param eval_output_df: DataFrame with optimal baseline data (LAI, WSO, DVS, SM columns)
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
    plt.show()

