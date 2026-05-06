import os

NUM_ENVIRONMENTS: int = 1 # Use -1 for automatic detection else use a positive integer

# RecurrentPPO hyperparameters
MODEL_CONFIG = {
    "policy": "MlpLstmPolicy",
    "learning_rate": 1e-4,
    "n_steps": 256,
    "batch_size": 128,
    "n_epochs": 10,
    "gamma": 0.99,
    "gae_lambda": 0.95,
    "clip_range": 0.2,
    "ent_coef": 0.01,
    "seed": 55
}

TRAINING_CONFIG = {
    "total_timesteps": 50000,
    "log_interval": 10,
    "n_envs": NUM_ENVIRONMENTS if NUM_ENVIRONMENTS>=0 else os.cpu_count() -1
}

CHECKPOINT_CONFIG = {
    "save_freq": 5000,
    "save_path": './logs/',
    "name_prefix": 'rppo_wofost'
}

EVAL_CONFIG = {
    "best_model_save_path": './logs/best_model',
    "log_path": './logs/eval',
    "eval_freq": 2000,
    "n_eval_episodes": 10,
    "deterministic": True,
    "render": False,
}
