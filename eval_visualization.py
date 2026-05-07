from functools import partial

import matplotlib.pyplot as plt
import numpy as np
from sb3_contrib import RecurrentPPO
from stable_baselines3.common.vec_env import VecNormalize, DummyVecEnv
from utils.env_factory import make_env


def evaluate_model(model, env, num_steps=150):
    obs = env.reset()

    # Recurrent PPO requires tracking the LSTM state
    lstm_states = None
    # Episode start signals for the LSTM
    episode_starts = np.atleast_1d(True)

    history = {
        'lai': [],
        'sm': [],
        'irrigation': [],
        'reward': []
    }

    for i in range(num_steps):
        # Predict action using the LSTM state
        action, lstm_states = model.predict(
            obs,
            state=lstm_states,
            episode_start=episode_starts,
            deterministic=True
        )

        obs, reward, done, info = env.step(action)
        episode_starts = np.atleast_1d(done)

        # Un-normalize the observation to get real physical values
        # This is crucial for plotting!
        real_obs = env.unnormalize_obs(obs)[0]

        history['lai'].append(real_obs[0])  # LAI
        history['sm'].append(real_obs[2])  # Soil Moisture
        history['irrigation'].append(float(action[0]))
        history['reward'].append(reward)

        if done:
            break

    return history


# Wrap it in a DummyVecEnv (SB3 models always expect a vectorized env)
env = DummyVecEnv([partial(make_env, verbose=1)])

# Load the normalization stats
env = VecNormalize.load("vec_normalize.pkl", env)

# Set to evaluation mode (stops updating the moving averages)
env.training = False
# Don't normalize the rewards during testing
env.norm_reward = False

# 4. LOAD THE TRAINED MODEL
model = RecurrentPPO.load("rppo_wofost_bangkok.zip", env=env)

print("Model and Stats loaded successfully!")

# 5. RUN THE EVALUATION LOOP
obs = env.reset()
lstm_states = None
episode_starts = np.atleast_1d(True)

history = {'lai': [], 'twso': [], 'dvs': [], 'sm': [], 'irrig': [], 'reward': [], 'dates': []}

dones = False
# Run for a full season (e.g., 150 days)
while not dones:
    # Predict with the LSTM
    action, lstm_states = model.predict(
        obs,
        state=lstm_states,
        episode_start=episode_starts,
        deterministic=True
    )

    obs, rewards, dones, info = env.step(action)
    episode_starts = np.atleast_1d(dones)

    # Get the "Un-normalized" observations for plotting
    # We use [0] because VecEnv always returns an array of observations
    real_obs = env.get_original_obs()[0]

    # Access TWSO (grain yield) and DVS (development stage) directly from the engine
    twso = env.envs[0].engine.get_variable("TWSO")
    twso_val = twso if twso is not None else 0.0
    dvs = env.envs[0].engine.get_variable("DVS")
    dvs_val = dvs if dvs is not None else 0.0

    history['lai'].append(real_obs[1])
    history['twso'].append(twso_val)
    history['dvs'].append(dvs_val)
    history['sm'].append(real_obs[2])
    history['irrig'].append(float(action[0][0]))
    history['reward'].append(rewards[0])

# 6. PLOT
plt.figure(figsize=(10, 12))
plt.subplot(5, 1, 1)
plt.plot(history['lai'], label='Leaf Area Index', color='green')
plt.legend()
plt.subplot(5, 1, 2)
plt.plot(history['twso'], label='Grain Yield (TWSO kg/ha)', color='orange')
plt.legend()
plt.subplot(5, 1, 3)
plt.plot(history['dvs'], label='Development Stage (DVS)', color='brown')
plt.axhline(y=1.0, color='gray', linestyle='--', alpha=0.5, label='Flowering')
plt.axhline(y=2.0, color='gray', linestyle='--', alpha=0.5, label='Maturity')
plt.legend()
plt.subplot(5, 1, 4)
plt.bar(range(len(history['irrig'])), history['irrig'], label='Irrigation (cm)', color='blue')
plt.plot(history['sm'], label='Soil Moisture', color='red', alpha=0.5)
plt.legend()
plt.subplot(5, 1, 5)
plt.plot(history['reward'], label='Reward', color='purple')
plt.legend()
plt.tight_layout()
plt.show()