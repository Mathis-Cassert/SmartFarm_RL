import pathlib
from datetime import datetime

from stable_baselines3.common.base_class import BaseAlgorithm
from stable_baselines3.common.vec_env import VecNormalize

from configs.save_config import MODEL_DIR

def save(model: BaseAlgorithm, env: VecNormalize = None, time_start: str = None) -> None:
    if time_start is None:
        time_start = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_folder: pathlib.Path = MODEL_DIR / f"{time_start}_{model.__class__.__name__}"
    model.save(save_folder / "model")
    if isinstance(env, VecNormalize):
        env.save(str(save_folder / "vec_normalize.pkl"))
