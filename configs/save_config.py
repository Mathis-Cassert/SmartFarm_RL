import pathlib
from configs.definition import ROOT_DIR

BASE_OUTPUT_DIR: pathlib.Path = ROOT_DIR / "output"

LOG_DIR: pathlib.Path = BASE_OUTPUT_DIR / "logs"
MODEL_DIR: pathlib.Path = BASE_OUTPUT_DIR / "models"