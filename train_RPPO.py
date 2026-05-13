import pathlib
from datetime import datetime

from stable_baselines3.common.base_class import BaseAlgorithm
from stable_baselines3.common.vec_env import VecEnv, VecNormalize
from stable_baselines3.common.env_util import make_vec_env

from utils.seed_utils import set_all_seeds
from utils.visualize_model import visualize_current_model
from training.rppo_trainer import train_rppo
from utils.env_factory import make_gym_env
from utils.save_model import save

verbose = 1
current_time: str = datetime.now().strftime("%Y%m%d_%H%M%S")
set_all_seeds(42, set_cuda_deterministic=False, verbose=verbose)

# Create environments
env : VecEnv = VecNormalize(make_vec_env(make_gym_env, env_kwargs={"verbose": verbose}, n_envs=1), norm_obs=True, norm_reward=True)
eval_env : VecEnv = VecNormalize(make_vec_env(make_gym_env, env_kwargs={"verbose": verbose}, n_envs=1), norm_obs=True, norm_reward=True)

# Train
model : BaseAlgorithm = train_rppo(env, eval_env, time_start=current_time, verbose=verbose)

# Save
save_folder: pathlib.Path = save(model, env if isinstance(env, VecNormalize) else None, time_start=current_time)

# Visual Evaluation
visualize_current_model(model, env, save_folder)

# Close environments
eval_env.close()
env.close()

