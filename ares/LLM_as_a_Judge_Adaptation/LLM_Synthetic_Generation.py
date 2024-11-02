from together import Together
from openai import AzureOpenAI
import os

def generate_synthetic_query_api_approach(document: str, synthetic_query_prompt: str, prompt: str, length_of_fewshot_prompt: int, 
                                          model_name: str, percentiles: list, 
                                          for_fever_dataset=False, for_wow_dataset=False,
                                          num_queries: int = 3) -> list:
    """
    Generates synthetic queries based on a document using an API model.

    This function constructs a prompt with the document and generates queries based on the specified dataset type.
    It handles token length limitations by truncating the document if necessary.

    Args:
        document (str): The document to base the query on.
        prompt (str): The initial prompt to the language model.
        length_of_fewshot_prompt (int): The number of few-shot examples already included in the prompt.
        model_name (str): The name of the API model to be used.
        percentiles (list): A list of percentiles for sampling during generation.
        for_fever_dataset (bool, optional): Flag to indicate if the function is used for the FEVER dataset. Defaults to False.
        for_wow_dataset (bool, optional): Flag to indicate if the function is used for the WoW dataset. Defaults to False.
        num_queries (int): Number of synthetic queries to generate per document.

    Returns:
        list: A list of synthetic queries generated by the model.
    """

    synthetic_queries = []

    # Construct the prompt without the document based on the dataset type
    prompt_without_document = prompt + "Example " + str(length_of_fewshot_prompt + 1) + ":\n"
    prompt_without_document += "Document:"

    # Calculate the length of tokens for the prompt and document
    max_tokens = 4096
    token_approx_factor = 4
    prompt_tokens_length = len(prompt_without_document) // token_approx_factor
    document_length = len(document) // token_approx_factor

    # Check if the total length exceeds the model's maximum input size and truncate if necessary
    if prompt_tokens_length + document_length + 100 >= max_tokens:
        truncated_document = document[:(max_tokens - prompt_tokens_length - 100) * token_approx_factor]
        prompt_with_document = prompt_without_document + truncated_document
    else:
        prompt_with_document = prompt_without_document + document

    # Add the final part of the prompt based on the dataset
    if for_fever_dataset:
        prompt_with_document += "\nStatement: "
    elif for_wow_dataset:
        prompt_with_document += "\nDialogue: "
    else:
        prompt_with_document += "\nQuestion: "

    TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

    client = Together(api_key=TOGETHER_API_KEY)
    
    # Generate queries for each percentile, repeating to reach num_queries
    for _ in range(num_queries):
        for percentile in percentiles:
            success = False
            for attempt in range(5):
                try:
                    chat_completion = client.chat.completions.create(
                        messages=[
                        {"role": "system", "content": synthetic_query_prompt},
                        {"role": "user", "content": prompt_with_document},
                    ],
                    model=model_name,
                    temperature=percentile,
                    stream=False
                )
                    final_response = chat_completion.choices[0].message.content

                    synthetic_queries.append(final_response)
                    success = True
                    break
                except Exception as e:
                    print(f"Error generating synthetic queries: {e}")

            if not success:
                print(f"Failed to generate synthetic queries after 5 attempts for percentile {percentile}")

    return synthetic_queries

def generate_synthetic_query_azure_approach(document: str, azure_openai_config: dict, synthetic_query_prompt: str, prompt: str,
                                          length_of_fewshot_prompt: int, percentiles: list, 
                                          for_fever_dataset=False, for_wow_dataset=False,
                                          num_queries: int = 3) -> list:
    """
    Generates synthetic queries based on a document using an Azure OpenAI model.

    This function constructs a prompt with the document and generates queries based on the specified dataset type.
    It handles token length limitations by truncating the document if necessary.

    Args:
        document (str): The document to base the query on.
        azure_openai_config (dict): Dictionary containing all information to use Azure OpenAI model.
        prompt (str): The initial prompt to the language model.
        length_of_fewshot_prompt (int): The number of few-shot examples already included in the prompt.
        percentiles (list): A list of percentiles for sampling during generation.
        for_fever_dataset (bool, optional): Flag to indicate if the function is used for the FEVER dataset. Defaults to False.
        for_wow_dataset (bool, optional): Flag to indicate if the function is used for the WoW dataset. Defaults to False.
        num_queries (int): Number of synthetic queries to generate per document.

    Returns:
        list: A list of synthetic queries generated by the model.
    """

    synthetic_queries = []

    # Construct the prompt without the document based on the dataset type
    prompt_without_document = prompt + "Example " + str(length_of_fewshot_prompt + 1) + ":\n"
    prompt_without_document += "Document:"

    # Calculate the length of tokens for the prompt and document
    max_tokens = 4096
    token_approx_factor = 4
    prompt_tokens_length = len(prompt_without_document) // token_approx_factor
    document_length = len(document) // token_approx_factor

    # Check if the total length exceeds the model's maximum input size and truncate if necessary
    if prompt_tokens_length + document_length + 100 >= max_tokens:
        truncated_document = document[:(max_tokens - prompt_tokens_length - 100) * token_approx_factor]
        prompt_with_document = prompt_without_document + truncated_document
    else:
        prompt_with_document = prompt_without_document + document

    # Add the final part of the prompt based on the dataset
    if for_fever_dataset:
        prompt_with_document += "\nStatement: "
    elif for_wow_dataset:
        prompt_with_document += "\nDialogue: "
    else:
        prompt_with_document += "\nQuestion: "

    # Setup the Azure OpenAI Model
    client = AzureOpenAI(
        api_key=azure_openai_config["api_key"],  
        api_version=azure_openai_config["model_version"],
        azure_endpoint = azure_openai_config["api_base"],
    )
    
    # Generate queries for each percentile, repeating to reach num_queries
    for _ in range(num_queries):
        for percentile in percentiles:
            success = False
            for attempt in range(5):
                try:
                    chat_completion = client.chat.completions.create(
                        model=azure_openai_config["deployment_name"],
                        messages=[
                            {"role": "system", "content": synthetic_query_prompt},
                            {"role": "user", "content": prompt_with_document},
                        ],
                        temperature=percentile,
                        stream=False
                    )
                    final_response = chat_completion.choices[0].message.content

                    synthetic_queries.append(final_response)
                    success = True
                    break
                except Exception as e:
                    print(f"Error generating synthetic queries: {e}")

            if not success:
                print(f"Failed to generate synthetic queries after 5 attempts for percentile {percentile}")

    return synthetic_queries

def generate_synthetic_answer_api_approach(document: str, question: str, synthetic_answer_prompt: str, prompt: str, 
                                           length_of_fewshot_prompt: int, model_name: str, for_fever_dataset=False, 
                                           for_wow_dataset=False): 
    # Construct the prompt without the document based on the dataset type
    prompt_without_document = prompt + "Example " + str(length_of_fewshot_prompt + 1) + ":\n"
    if for_fever_dataset:
        prompt_without_document += "Document: \nStatement: \nAnswer: "
    elif for_wow_dataset:
        prompt_without_document += "Document: \nDialogue: \nResponse: "
    else:
        prompt_without_document += "Document: \nQuestion: \nAnswer: "

    prompt_tokens_length = len(prompt_without_document)
    document_length = len(document)
    question_length = len(question)

    if prompt_tokens_length + document_length + question_length + 100 >= 4096:
        truncated_document = document[:4096 - prompt_tokens_length - question_length - 100]
        prompt = prompt_without_document + truncated_document
    else: 
        prompt = prompt_without_document + document 
    
    prompt += "Example" + str(length_of_fewshot_prompt + 1) + ":\n"
    prompt += "Document: " + document + "\n"
    if for_fever_dataset:
        prompt += "Statement: " + question + "\n"
        prompt += "Answer: "
    elif for_wow_dataset:
        prompt += "Dialogue: " + question + "\n"
        prompt += "Response: "
    else:
        prompt += "Question: " + question + "\n"
        prompt += "Answer: "

    TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

    client = Together(api_key=TOGETHER_API_KEY)
    
    for attempt in range(5):
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                {"role": "system", "content": synthetic_answer_prompt},
                {"role": "user", "content": prompt},
            ],
            model=model_name,
            stream=False
        )
            # responses = []
            
            # for chunk in chat_completion:
            #     responses.append(chunk.choices[0].delta.content)

            # final_response = " ".join(responses)

            final_response = chat_completion.choices[0].message.content
            
            return final_response
        except Exception as e:
            print(f"Error generating synthetic queries: {e}")
            continue

def generate_synthetic_answer_azure_approach(document: str, question: str, synthetic_answer_prompt: str, prompt: str, 
                                           length_of_fewshot_prompt: int, azure_openai_config: dict, for_fever_dataset=False, 
                                           for_wow_dataset=False): 
    # Construct the prompt without the document based on the dataset type
    prompt_without_document = prompt + "Example " + str(length_of_fewshot_prompt + 1) + ":\n"
    if for_fever_dataset:
        prompt_without_document += "Document: \nStatement: \nAnswer: "
    elif for_wow_dataset:
        prompt_without_document += "Document: \nDialogue: \nResponse: "
    else:
        prompt_without_document += "Document: \nQuestion: \nAnswer: "

    prompt_tokens_length = len(prompt_without_document)
    document_length = len(document)
    question_length = len(question)

    if prompt_tokens_length + document_length + question_length + 100 >= 4096:
        truncated_document = document[:4096 - prompt_tokens_length - question_length - 100]
        prompt = prompt_without_document + truncated_document
    else: 
        prompt = prompt_without_document + document 
    
    prompt += "Example" + str(length_of_fewshot_prompt + 1) + ":\n"
    prompt += "Document: " + document + "\n"
    if for_fever_dataset:
        prompt += "Statement: " + question + "\n"
        prompt += "Answer: "
    elif for_wow_dataset:
        prompt += "Dialogue: " + question + "\n"
        prompt += "Response: "
    else:
        prompt += "Question: " + question + "\n"
        prompt += "Answer: "

    # Setup the Azure OpenAI Model
    client = AzureOpenAI(
        api_key=azure_openai_config["api_key"],  
        api_version=azure_openai_config["model_version"],
        azure_endpoint = azure_openai_config["api_base"],
    )
    
    for attempt in range(5):
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": synthetic_answer_prompt},
                    {"role": "user", "content": prompt},
                ],
                model=azure_openai_config["deployment_name"],
                stream=False
            )
            # responses = []
            
            # for chunk in chat_completion:
            #     responses.append(chunk.choices[0].delta.content)

            # final_response = " ".join(responses)

            final_response = chat_completion.choices[0].message.content
            
            return final_response
        except Exception as e:
            print(f"Error generating synthetic queries: {e}")
            continue

def generate_synthetic_contradictory_answers_api_approach(document: str, question: str, synthetic_contradictory_answer_prompt: str, fewshot_examples: str, 
                                           model_name: str, for_fever_dataset=False, for_wow_dataset=False) -> str:
    """
    Generates a synthetic contradictory answer using an API-based approach based on the provided document and question.

    This function constructs a prompt dynamically based on whether it is being used for the FEVER or WoW dataset,
    or a general dataset. It then sends the prompt to the API to generate a contradictory answer.

    Args:
        document (str): The document text based on which the contradictory answer is to be generated.
        question (str): The question text based on the document.
        synthetic_answer_prompt (str): The initial prompt text to which the document and question will be appended.
        fewshot_examples (str): Few-shot examples to include in the prompt for the API.
        api_url (str): The API endpoint URL.
        api_key (str): The API key for authentication.
        model_name (str): The model name to be used in the API.
        for_fever_dataset (bool, optional): Flag to indicate if the function is being used for the FEVER dataset. Defaults to False.
        for_wow_dataset (bool, optional): Flag to indicate if the function is being used for the WoW dataset. Defaults to False.

    Returns:
        str: The generated contradictory answer text.
    """

    prompt = synthetic_contradictory_answer_prompt + fewshot_examples
    prompt += "Example " + str(prompt.count("Example") + 1) + ":\n"
    if for_fever_dataset:
        prompt += "Document: \nStatement: \nIncorrect Answer: "
    elif for_wow_dataset:
        prompt += "Document: \nDialogue: \nIncorrect Response: "
    else:
        prompt += "Document: \nQuestion: \nIncorrect Answer: "

    prompt_token_length = len(prompt)
    document_token_length = len(document)
    question_token_length = len(question)

    if prompt_token_length + document_token_length + question_token_length + 100 >= 4096:
        truncated_document = document[:4096 - prompt_token_length - question_token_length - 100]
        prompt += truncated_document
    else: 
        prompt += document
    
    prompt += "Example " + str(prompt.count("Example") + 1) + ":\n"
    prompt += "Document: " + document + "\n"
    if for_fever_dataset:
        prompt += "Statement: " + question + "\n"
        prompt += "Incorrect Answer: "
    elif for_wow_dataset:
        prompt += "Dialogue: " + question + "\n"
        prompt += "Incorrect Response: "
    else:
        prompt += "Question: " + question + "\n"
        prompt += "Incorrect Answer: "
    
    TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

    client = Together(api_key=TOGETHER_API_KEY)
    
    for attempt in range(5):
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                {"role": "system", "content": synthetic_contradictory_answer_prompt},
                {"role": "user", "content": prompt},
            ],
            model=model_name,
            stream=False
        )
            # responses = []
            
            # for chunk in chat_completion:
            #     responses.append(chunk.choices[0].delta.content)

            # final_response = " ".join(responses)

            final_response = chat_completion.choices[0].message.content

            return final_response
        except Exception as e:
            print(f"Error generating synthetic contradictory answer: {e}")
            continue