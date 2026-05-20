import pathlib

from stable_baselines3.common.base_class import BaseAlgorithm
from stable_baselines3.common.vec_env import VecEnv

from utils.eval_utils import plot_evaluation_results, evaluate_model, initiate_eval_model
from utils.seed_utils import set_all_seeds


def visualize_saved_model(folder_name: str, use_log: bool = False, step: int = 0, verbose: int = 0) -> None:
    """
    Save figure about a trained model for visual evaluation of it's performance

    :param folder_name: Name of the folder containing the model and environment files (e.g. 20260511_172544_RecurrentPPO)
    :param use_log: If True use the model in the log folder instead of the final model
    :param step: Number of steps of the model to evaluate (-1 for the best model). Only used if use_log is True
    :param verbose: Verbosity level for the environment (0=no output, 1=basic output, 2=debug output)
    """
    # Initiate evaluation model
    model, env, model_folder, is_best = initiate_eval_model(folder_name, use_log=use_log, step=step, verbose=verbose)

    # Evaluate model
    history, eval_output_df, eval_summary_df = evaluate_model(model, env)

    # Plot evaluation results
    plot_evaluation_results(history, eval_output_df, model_folder, prefix=str(step) if not is_best else '')

    # Close environments
    env.close()

def visualize_current_model(model: BaseAlgorithm, env: VecEnv, model_folder: pathlib.Path) -> None:
    """
    Save figure about a current model for visual evaluation of it's performance
    :param model: The model to evaluate
    :param env: The environment to evaluate the model in
    :param model_folder: Path to the folder where the figure will be saved
    """
    # Evaluate model
    history, eval_output_df, eval_summary_df = evaluate_model(model, env)

    # Plot evaluation results
    plot_evaluation_results(history, eval_output_df, model_folder)

    # Close environments
    env.close()

if __name__ == '__main__':
    set_all_seeds(None, set_cuda_deterministic=True)
    visualize_saved_model("20260514_163148_RecurrentPPO", use_log=True, step=-1, verbose=2)
