from utils.eval_utils import plot_evaluation_results, evaluate_model, initiate_eval_model

verbose = 0

# Initiate evaluation model
model, env = initiate_eval_model("output/models/20260509_120439_RecurrentPPO", verbose)

# Evaluate model
history, eval_output_df, eval_summary_df = evaluate_model(model, env)

# Plot evaluation results
plot_evaluation_results(history, eval_output_df)