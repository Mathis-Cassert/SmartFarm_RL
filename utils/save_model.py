import pathlib
from datetime import datetime

from stable_baselines3.common.base_class import BaseAlgorithm
from stable_baselines3.common.vec_env import VecNormalize

from configs.save_config import MODEL_DIR

def save(model: BaseAlgorithm, env: VecNormalize = None, time_start: str = None) -> pathlib.Path:
    """
    Save the model and environment to disk
    :param model: The model to save
    :param env: The environment to save only if it is a VecNormalize instance
    :param time_start: The starting time to use for the save folder
    :return: The path to the save folder
    """
    if time_start is None:
        time_start = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_folder: str = f"{time_start}_{model.__class__.__name__}"
    save_path: pathlib.Path = MODEL_DIR / model_folder
    model.save(save_path / "model")
    if isinstance(env, VecNormalize):
        env.save(str(save_path / "vec_normalize.pkl"))

    return save_path
