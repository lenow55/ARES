from ares.RAG_Automatic_Evaluation.LLMJudge_RAG_Compared_Scoring import begin
from ares.RAG_Automatic_Evaluation.LLMJudge_RAG_Compared_Scoring import filter_dataset
from ares.RAG_Automatic_Evaluation.LLMJudge_RAG_Compared_Scoring import preprocess_data
from ares.RAG_Automatic_Evaluation.LLMJudge_RAG_Compared_Scoring import load_api_model 
from ares.RAG_Automatic_Evaluation.LLMJudge_RAG_Compared_Scoring import load_tokenizer_and_model
from ares.RAG_Automatic_Evaluation.LLMJudge_RAG_Compared_Scoring import evaluate_model
from ares.RAG_Automatic_Evaluation.LLMJudge_RAG_Compared_Scoring import post_process_predictions
from ares.RAG_Automatic_Evaluation.LLMJudge_RAG_Compared_Scoring import evaluate_and_scoring_data

machine_label_system_prompt = (
    "Given the following question and document, you must analyze the provided document "
    "and determine whether it is sufficient for answering the question. In your evaluation, "
    "you should consider the content of the document and whether it contains the answer to "
    "the provided question. Output your final verdict by strictly following this format: "
    "'[[Yes]]' if the document is sufficient and '[[No]]' if the document provided is not sufficient."
)

def rag_scoring_config(alpha, num_trials, evaluation_datasets, few_shot_examples_filepath, checkpoints, labels,
model_choice, llm_judge, assigned_batch_size, number_of_labels, gold_label_path, rag_type, vllm, host_url, request_delay, debug_mode, 
machine_label_llm_model, gold_machine_label_path):
    
    # Validate if either gold_label_path or gold_machine_label_path is provided
    if not gold_label_path and not gold_machine_label_path:
        raise ValueError("Either 'gold_label_path' or 'gold_machine_label_path' must be provided.")

    # Validate inputs and determine model loading strategy
    if checkpoints:
        if llm_judge and llm_judge != "None":
            print("Warning: Both checkpoint and llm_judge were provided. Using checkpoints.")
        model_loader = lambda chk: load_tokenizer_and_model(model_choice, number_of_labels, chk)
    elif llm_judge and llm_judge != "None":
        model_loader = lambda _: load_api_model(llm_judge, vllm)
    else:
        raise ValueError("No valid model or checkpoint provided.")

    # Use zip only if checkpoints are not empty, otherwise assume only llm_judge is used
    if checkpoints:
        # Here we assume that the length of checkpoints and labels is the same
        pairings = zip(checkpoints, labels)
    else:
        # If no checkpoints, create dummy pairs for labels with None for checkpoint
        pairings = ((None, label) for label in labels)

    for checkpoint, label_column in pairings:
        LLM_judge_ratio_predictions = []
        validation_set_lengths = []
        validation_set_ratios = []
        ppi_confidence_intervals = []
        accuracy_scores = []
        for test_set_selection in evaluation_datasets:

            few_shot_examples = begin(evaluation_datasets, checkpoints, labels, few_shot_examples_filepath)

            context_relevance_system_prompt, answer_faithfulness_system_prompt, answer_relevance_system_prompt = filter_dataset(rag_type)
            
            test_set, text_column = preprocess_data(test_set_selection, label_column, labels)

            model, tokenizer, device = model_loader(checkpoint)
            
            eval_model_settings = {
                "test_set": test_set,
                "label_column": label_column,
                "text_column": text_column,
                "device": device,
                "checkpoint": checkpoint,
                "tokenizer": tokenizer,
                "model": model,
                "assigned_batch_size": assigned_batch_size,
                "model_choice": model_choice,
                "context_relevance_system_prompt": context_relevance_system_prompt,
                "answer_faithfulness_system_prompt": answer_faithfulness_system_prompt,
                "answer_relevance_system_prompt": answer_relevance_system_prompt,
                "few_shot_examples_filepath": few_shot_examples_filepath,
                "llm_judge": llm_judge,
                "vllm": vllm,
                "host_url": host_url,
                "request_delay": request_delay,
                "debug_mode": debug_mode
            }

            total_predictions, total_references, results, metric = evaluate_model(eval_model_settings)
            
            post_process_settings = {
                "checkpoint": checkpoint,
                "test_set": test_set,
                "label_column": label_column,
                "total_predictions": total_predictions,
                "labels": labels,
                "gold_label_path": gold_label_path,
                "tokenizer": tokenizer,
                "assigned_batch_size": assigned_batch_size,
                "device": device,
                "gold_machine_label_path": gold_machine_label_path,
                "machine_label_system_prompt": machine_label_system_prompt,
                "machine_label_llm_model": machine_label_llm_model,
                "vllm": vllm,
                "host_url": host_url,
                "debug_mode": debug_mode,
                "request_delay": request_delay,
                "few_shot_examples": few_shot_examples
            }

            test_set, Y_labeled_dataset, Y_labeled_dataloader, Y_labeled_predictions, Yhat_unlabeled_dataset, prediction_column = post_process_predictions(post_process_settings) 
            
            evaluate_scoring_settings = {
                "test_set": test_set,
                "Y_labeled_predictions": Y_labeled_predictions,
                "Y_labeled_dataset": Y_labeled_dataset,
                "Y_labeled_dataloader": Y_labeled_dataloader,
                "Yhat_unlabeled_dataset": Yhat_unlabeled_dataset,
                "alpha": alpha,
                "num_trials": num_trials,
                "model": model,
                "device": device,
                "model_choice": model_choice,
                "context_relevance_system_prompt": context_relevance_system_prompt,
                "answer_faithfulness_system_prompt": answer_faithfulness_system_prompt,
                "answer_relevance_system_prompt": answer_relevance_system_prompt,
                "few_shot_examples": few_shot_examples,
                "metric": metric,
                "prediction_column": prediction_column,
                "label_column": label_column,
                "test_set_selection": test_set_selection,
                "LLM_judge_ratio_predictions": LLM_judge_ratio_predictions,
                "validation_set_lengths": validation_set_lengths,
                "validation_set_ratios": validation_set_ratios,
                "ppi_confidence_intervals": ppi_confidence_intervals,
                "accuracy_scores": accuracy_scores,
                "results": results,
                "checkpoint": checkpoint,
                "llm_judge": llm_judge,
                "vllm": vllm,
                "host_url": host_url,
                "request_delay": request_delay,
                "debug_mode": debug_mode
            }
            
            evaluate_and_scoring_data(evaluate_scoring_settings)

# if not checkpoints and not llm_judge:
#         raise ValueError("Either checkpoints or an llm_model must be provided.")

#     if checkpoints:
#         if len(checkpoints) != len(evaluation_datasets):
#             raise ValueError("The number of checkpoints must match the number of evaluation datasets.")
#         models_to_use = checkpoints
#     else:
#         models_to_use = [llm_judge] * len(evaluation_datasets)

#     for model_to_use, test_set_selection in zip(models_to_use, evaluation_datasets):
#         for label_column in labels:
#             LLM_judge_ratio_predictions = []
#             validation_set_lengths = []
#             validation_set_ratios = []
#             ppi_confidence_intervals = []
#             accuracy_scores = []

#             few_shot_examples = begin(evaluation_datasets, model_to_use, labels, GPT_scoring, few_shot_examples_filepath)

#             context_relevance_system_prompt, answer_faithfulness_system_prompt, answer_relevance_system_prompt = filter_dataset(rag_type)
            
#             test_set, text_column = preprocess_data(test_set_selection, label_column, labels)

#             model, tokenizer, device = load_model(llm_judge, number_of_labels, GPT_scoring, model_to_use) 

#             total_predictions, total_references, results, metric = evaluate_model(test_set, label_column, text_column, device, GPT_scoring, tokenizer, model, assigned_batch_size, llm_judge, context_relevance_system_prompt, answer_faithfulness_system_prompt, answer_relevance_system_prompt)

#             test_set, Y_labeled_dataset, Y_labeled_dataloader, Y_labeled_predictions, Yhat_unlabeled_dataset, prediction_column = post_process_predictions(test_set, label_column, total_predictions, labels, use_pseudo_human_labels, gold_label_path, tokenizer, assigned_batch_size, device) 

#             evaluate_and_scoring_data(test_set, Y_labeled_predictions, Y_labeled_dataset, Y_labeled_dataloader, Yhat_unlabeled_dataset, alpha, num_trials, model, device, llm_judge, 
#             annotated_datapoints_filepath, context_relevance_system_prompt, answer_faithfulness_system_prompt, answer_relevance_system_prompt,
#             few_shot_examples, metric, prediction_column, label_column, test_set_selection, 
#             LLM_judge_ratio_predictions, validation_set_lengths, validation_set_ratios, 
#             ppi_confidence_intervals, accuracy_scores, results)