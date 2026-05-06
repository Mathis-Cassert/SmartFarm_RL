from utils.env_factory import make_env
from training.rppo_trainer import train_rppo
from stable_baselines3.common.vec_env import VecNormalize, VecEnvWrapper
from stable_baselines3.common.env_util import make_vec_env
from sb3_contrib import RecurrentPPO

verbose = 1

# Create environments
env : VecEnvWrapper = VecNormalize(make_vec_env(make_env, env_kwargs={"verbose": verbose}, n_envs=1), norm_obs=True, norm_reward=True)
eval_env : VecEnvWrapper = VecNormalize(make_vec_env(make_env, env_kwargs={"verbose": verbose}, n_envs=1), norm_obs=True, norm_reward=True)

# Train
model : RecurrentPPO = train_rppo(env, eval_env, verbose=verbose)

# Save
model.save("rppo_wofost_bangkok")
env.save("vec_normalize.pkl")