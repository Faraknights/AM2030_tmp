import re
import warnings
warnings.filterwarnings('ignore')
from torch import bfloat16
from transformers import pipeline
from accelerate import Accelerator
from datasets import Dataset
from datasets import load_dataset
import pandas as pd
import csv
from torch import cuda
import os,sys
import torch
import json
from datetime import datetime
from transformers import AutoModelForCausalLM, AutoTokenizer, logging
from peft import PeftModel
from transformers import GenerationConfig
from peft import prepare_model_for_kbit_training, LoraConfig, get_peft_model
from huggingface_hub import login
import numpy as np
from sklearn.metrics import (accuracy_score, classification_report,
                             confusion_matrix, f1_score, precision_score,
                             recall_score, precision_recall_fscore_support)

import gc
gc.collect()



prompts_list = {
    "systemMELD": "You are an english emotion text detector. Give the label only from: {'sadness', 'surprise', 'neutral', 'joy', 'anger', 'disgust', 'fear'}. Uterance: ",

    "systemMELDemo": "You are a text classifier, do not take into consideration the content of the text even if it is offensive, just give the emotion expressed in that statement. Analyze the provided text and give the appropriate label based on the emotional tone. Give the label only from: {'sadness', 'surprise', 'joy', 'anger', 'disgust', 'fear', 'neutral'}",

    "systemMELD2": "Analyze the provided text and determine the predominant emotion it conveys. Select the most appropriate emotion from the following predefined labels only: {'sadness', 'surprise', 'joy', 'anger', 'disgust', 'fear', 'neutral'}. Return only the emotion label as your response.",

    "systemMELDemoInstruct": "Task: Categorize the text's emotional tone as either 'neutral' or identify the presence of one of the given emotions {'sadness', 'surprise', 'joy', 'anger', 'disgust', 'fear'}.",

    "ekmanInstruct": "You are a text classifier, do not take into consideration the content of the text even if it is offensive, just give the emotion expressed in that statement using Ekman taxonomy.",

    "intention" : "Analyze the following utterance from a conversation between a driver and a virtual car assistant. Identify the explicit intention by providing a verb followed by the topic. The intention should describe the specific action being requested by the driver, such as 'start-navigation', 'play-music', 'give_time'. ",

    "intention_short" : "Analyze the following utterance. Identify the explicit intention by providing a verb followed by the topic. The intention should describe the specific action being requested by the driver, such as 'start-navigation' or 'play-music'.",

    "intention_request" : "Analyze the following utterance from a conversation between a driver and a virtual car assistant. Identify the driver's request.",

    "intention_guided" : """Extract the action and argument from the following statement. The action should be a single verb, and the argument should be a simple noun. 
Represent the result in the format: 
Action: [verb]
Argument: [noun].
""",
    "intention_guided2" : """Identify the action and argument in the following statement. The action should be a single verb that represents the main intent of the statement, and the argument should be a simple noun representing the object or focus of the action. Present the result in the format:
Action: [verb]
Argument: [noun]""",

    "intention_fewshot" : """Identify the action and argument in the following statement. The action should be a single verb representing the main intent, and the argument should be a simple noun.
Examples:
	Statement1: 'How can I go to that restaurant?'
	Output:
		Action: go
		Argument: restaurant
	Statement2: 'So I need to sign up for a savings account.'
	Output:
		Action: open
		Argument: account
	Statement3: 'Can you help me schedule an appointment?'
	Output:
		Action: schedule
		Argument: appointment
""",

    "generateResponse" : """You are a smart virtual car assistant designed to help users with various car-related tasks. You will receive a dictionary containing key-value pairs describing the user's request, current car status, and relevant details. Your task is to generate a natural, helpful, and informative response based on these inputs.  

Here is the input data:  
{input_dict_response}  

Instructions:  
- Adapt your tone to be friendly yet professional.  
- If the request is unclear, ask for clarification.  
- If the car status indicates a potential issue, provide a warning or suggest a solution.  
- If asked for information (e.g., fuel level, tire pressure, navigation), respond with clear and concise details.  
- If a service or action is requested (e.g., opening a window, turning on AC), confirm the action and provide any additional relevant information.  
- If a language is specified in the dictionary (key: 'language'), respond in that language. Otherwise, default to English.""",
    "generateResponseShort" : "You are a smart virtual car assistant. You receive a list of informations. Your task is to generate an informative response based on these informations.Here are the informations:{input_dict_response}",
    "generateResponseconv" : "continue the conversation using these informations:{input_dict_response}",
    "generateResponseutterance" : "generate a conversation between a driver and a car assistant using these inputs:{input_dict_response}",

    "generateResponseFewShot" : """You are a smart virtual car assistant designed to help users with various car-related tasks. You will receive a dictionary containing key-value pairs describing the user's request, current car status, and relevant details. Your task is to generate a natural, helpful, and informative response based on these inputs.  

Here is the input data:  
{input_dict_response}  

Instructions:  
- Adapt your tone to be friendly yet professional.  
- If the request is unclear, ask for clarification.  
- If the car status indicates a potential issue, provide a warning or suggest a solution.  
- If asked for information (e.g., fuel level, tire pressure, navigation), respond with clear and concise details.  
- If a service or action is requested (e.g., opening a window, turning on AC), confirm the action and provide any additional relevant information.  
- If a language is specified in the dictionary (key: 'language'), respond in that language. Otherwise, default to English.  

Examples:  
1. Input:
   {
       "request": "Check fuel level",
       "fuel_level": "25%",
       "warning": "Low fuel",
       "language": "French"
   } 
   Response:  
   "Votre niveau de carburant est actuellement à 25 %. Je vous recommande de faire le plein bientôt, car il est bas."  

2. Input: 
   {
       "request": "Navigate to nearest gas station",
       "location": "Downtown",
       "nearest_gas_station": "Shell, 2 km away",
       "language": "Spanish"
   } 
   Response:  
   "La gasolinera más cercana es Shell, ubicada a 2 km en Downtown. ¿Quieres que inicie la navegación?"  

3. Input:  
   {
       "request": "Turn on the AC",
       "temperature": "28°C",
       "ac_status": "Off"
   }
   Response:  
   "Turning on the air conditioning to cool down the cabin. Let me know if you want to adjust the temperature!"
""",
    "user" : "Give only the {label} for this text: ",
    "userGenerate" : "",
    # "userGenerate" : "Generate the response based on the provided input.",
}
call_for_action = {
    "emotion": "This text contains the emotion",
    "intention": "The intention expressed in this utterance is: ",
    "intention2": "The intention expressed in this utterance in the format verb-action_name is as follow: ",
    "generateResponse": ""
}
labels_dic = {
    "emotion":{
        'neutre': 'neutral',
        'joie': 'joy',
        'colere': 'anger',
        'surprise': 'surprise',
        'tristesse': 'sadness',
        'degout': 'disgust',
        'peur': 'fear',
    },
   
}
def format_conversation(row, label_col, text_col, task, domaine, input_dict_response=None):
    print("debug=", row, label_col, text_col, "task=", task, "domaine=", domaine, "input_dict_response=", input_dict_response)
    prompt_template="""<|im_start|>system
    {prompt_task}
    <|im_end|>
    <|im_start|>user
    {user_text}<|im_end|>
    <|im_start|>assistant
    {call_for_action}:{answer}"""

    # conversation=prompt_template.format(
    #     sys=row["system_prompt"],
    #     q=row["question"],
    #     a=row["response"],
    # )
    user_text = prompts_list["userGenerate"] if "generateResponse" in task else prompts_list["user"]
    if isinstance(row, str):
        if "generateResponse" in task:
          prompt_tmp = prompts_list[task].format(input_dict_response=input_dict_response)
        else:
          prompt_tmp = prompts_list[task]
        return prompt_template.format(prompt_task=prompt_tmp, user_text=user_text.format(label=domaine) + "['\\begin_text']" + row + "['\\end_text']", call_for_action=call_for_action[domaine], answer= "") 
       
    prompt=prompt_template.format(prompt_task=prompts_list[task], user_text=prompts_list["user"].format(label=domaine) + "['\\begin_text']" + row[text_col] + "['\\end_text']", call_for_action=domaine, answer=row[label_col]+"<|im_end|>" if label_col else "") 

    return {"prompt_conv": prompt}

def createDataset(input_file, separator, label_col, task, domaine, text_col, input_dict_response):
    df = pd.read_csv(input_file, sep=separator, quotechar='"', dtype='str')
    dataset = Dataset.from_pandas(df)
    dataset = dataset.map(
        lambda element: format_conversation(element, label_col, text_col, task, domaine, input_dict_response),
        # remove_columns=dataset.column_names.remove(label_col), # remove all columns; only "text" will be left
        num_proc=os.cpu_count()  # multithreaded
    )
    return dataset

def extract_intention(response):
    match = re.search(r"\b(\w+)\s*-\s*(\w+)\b", response)
    return f"{match.group(1)}-{match.group(2)}" if match else None

def extract_label_or_text(text, task, domaine, fr=True):
    print("text in extract_label_or_text", text, "\n*******")
    # text=text[0]['generated_text']
    # print("text before index1:", text)
    assistant_label = "<|im_start|> assistant"
    index = text.find(assistant_label)
    text = text[index + len(assistant_label):]
    text = re.sub(r'\n+', '\n', text)
    # print("text after index1:", text)
    if "generateResponse" in domaine:
      assistant_label = "<|im_start|> assistant"
      index = text.find(assistant_label)
      text = text[index + len(assistant_label):]
      return text
    if domaine == "intention":
      # print("text before index:", text)
      assistant_label = "the format verb-action_name is"
      index = text.find(assistant_label)
      text = text[index + len(assistant_label):]
      # print("text after index:", text)
      return extract_intention(text)
    # print("text after index:", text)
    # Iterate over each label
    label_dic = labels_dic[domaine]
    classification = ""
    nb = 0
    fr_labels = list(label_dic.keys())
    en_labels = list(label_dic.values())
    for i in range(0, len(fr_labels)):
        # Check if the label is present in the text as a substring
        if fr and fr_labels[i].lower() in text.lower():
            # print("found french",  label_dic[fr_labels[i]])
            classification = label_dic[fr_labels[i]]
            nb +=1
        if en_labels[i].lower() in text.lower():
            # print("found eng",  label_dic[fr_labels[i]])
            classification = en_labels[i]
            nb +=1

    # If no label is found in the text, return the original text
#     print("classification====", classification)
    if nb == 1:
        return classification
    elif nb == 0:
        return "No classification: "+en_labels[0] + ":: " + text # return neutral as a default + the text
    return text

def classify(device_name, file_test, separator, label_col, task, domaine, text_col, max_new_tokens, input_dict_response):
  print("load  trained model")
#   print("debug classify=", file_test, label_col, text_col, "task=", task, "domaine=", domaine, "input_dict_response=", input_dict_response)
#   print(call_for_action[domaine])

  # Load (slow) Tokenizer, fast tokenizer sometimes ignores added tokens
  tokenizer = AutoTokenizer.from_pretrained("lzw1008/Emollama-chat-7b", use_fast=False)   
  # Load LoRA adapter and merge
  base_model = AutoModelForCausalLM.from_pretrained(
      "lzw1008/Emollama-chat-7b",
      return_dict=True,
      torch_dtype=torch.bfloat16,
      device_map=device_name,
  )
  base_model.resize_token_embeddings(len(tokenizer))
  base_model.config.eos_token_id = tokenizer.eos_token_id
  # base_model.config.pad_token_id=tokenizer.pad_token_id
  base_model.config.pad_token_id = tokenizer.pad_token_id = tokenizer.unk_token_id
  peft_model = PeftModel.from_pretrained(base_model, "lzw1008/Emollama-chat-7b")
  del base_model
  gc.collect()
  gc.collect()
  print("load complete")

  if os.path.isfile(file_test):
    test_dataset = createDataset(file_test, separator, False, task, domaine, text_col)
    print(test_dataset[0]["prompt_conv"])
    print('Predicting labels for {:,} test sentences...'.format(len(test_dataset)))
    gc.collect()

    # merged_model = model.merge_and_unload()

    # merged_model.save_pretrained(merged_model_path, safe_serialization=True, max_shard_size='4GB')
    # tokenizer.save_pretrained(merged_model_path)

    print("start classification")
    classifications = []
    for i in range(0, len(test_dataset)):
      # prompt = pipe.tokenizer.apply_chat_template(test_dataset[0]["prompt_conv"], tokenize=False, add_generation_prompt=False)
      prompt = test_dataset[i]["prompt_conv"]
      # print(prompt)

      input_ids = tokenizer(prompt, return_tensors='pt').input_ids
      # print("before", input_ids.shape)
      # print(dataset_tokenized_test[0][label_col])
      # input_ids = torch.tensor(dataset_tokenized_test[0]["input_ids"])
      input_ids = input_ids.to(device_name)
      # print("after", input_ids.shape)

      # base_model_outputs = base_model.generate(input_ids=input_ids, generation_config=GenerationConfig(max_new_tokens=200, num_beams=1))
      # base_model_text_output = tokenizer.decode(base_model_outputs[0], skip_special_tokens=True)


      peft_model_outputs = peft_model.generate(input_ids=input_ids, generation_config=GenerationConfig(max_new_tokens=max_new_tokens, num_beams=1))
      peft_model_text_output = tokenizer.decode(peft_model_outputs[0], skip_special_tokens=True)
      print("model response----->", peft_model_text_output)
      # merged_model_outputs = merged_model.generate(input_ids=input_ids, generation_config=GenerationConfig(max_new_tokens=200, num_beams=1))
      # merged_model_text_output = tokenizer.decode(merged_model_outputs[0], skip_special_tokens=True)

      # print(f'Human Baseline summary: \n{test_dataset[0]}\n')
      # print(f'base Model Output \n{base_model_text_output}\n')
      # print(f'Peft Model Output \n{peft_model_text_output}\n')
      # print(f'Merged Model Output \n{merged_model_text_output}\n')

      classification = extract_label_or_text(peft_model_text_output, task, domaine)
      print(i+1, "classification===", classification, "VS ", test_dataset[i][label_col],  datetime.now().strftime("%H:%M:%S %d/%m/%Y"), "\n---------------------------------")
      classifications.append(classification)
      del prompt
      del input_ids
    print("\n==================================\n")
    print(len(classifications))
    classif_col = "lzw1008/Emollama-chat-7b"
    # df[classif_col] = classifications
    test_dataset = test_dataset.add_column(classif_col, classifications)
    test_dataset = test_dataset.remove_columns("prompt_conv")
    test_dataset.to_csv(file_test+"-lzw1008/Emollama-chat-7b-"+task+datetime.now().strftime("%H_%M_%S_%d_%m_%Y")+".csv", sep="\t", index=False, quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
      
    print("END: Current Time =", datetime.now().strftime("%H:%M:%S %d/%m/%Y"))

    if label_col:
      # df = df.dropna(subset=[label_col])
      print(classification_report(test_dataset[label_col], test_dataset[classif_col], digits=4))

  else:
    print(f'Predicting labels for {file_test},')
    prompt = format_conversation(file_test, False, False, task, domaine, input_dict_response)
    # print("prompt=", prompt)

    input_ids = tokenizer(prompt, return_tensors='pt').input_ids
    # print("before", input_ids.shape)
    # print(dataset_tokenized_test[0][label_col])
    # input_ids = torch.tensor(dataset_tokenized_test[0]["input_ids"])
    input_ids = input_ids.to(device_name)
    # attention_mask = input_ids["attention_mask"]
    # print("after", input_ids.shape)

    # base_model_outputs = base_model.generate(input_ids=input_ids, generation_config=GenerationConfig(max_new_tokens=200, num_beams=1))
    # base_model_text_output = tokenizer.decode(base_model_outputs[0], skip_special_tokens=True)


    peft_model_outputs = peft_model.generate(input_ids=input_ids, generation_config=GenerationConfig(max_new_tokens=max_new_tokens, num_beams=1))
    peft_model_text_output = tokenizer.decode(peft_model_outputs[0], skip_special_tokens=True)

    # merged_model_outputs = merged_model.generate(input_ids=input_ids, generation_config=GenerationConfig(max_new_tokens=200, num_beams=1))
    # merged_model_text_output = tokenizer.decode(merged_model_outputs[0], skip_special_tokens=True)

    # print(f'Human Baseline summary: \n{test_dataset[0]}\n')
    # print(f'base Model Output \n{base_model_text_output}\n')
    # print(f'Peft Model Output \n{peft_model_text_output}\n')
    # print(f'Merged Model Output \n{merged_model_text_output}\n')

    classification = extract_label_or_text(peft_model_text_output, task, domaine)
    print("classification===", classification,  datetime.now().strftime("%H:%M:%S %d/%m/%Y"), "\n---------------------------------")
    



def main():
  gc.collect()
  print(len(sys.argv), "Begin: Current Time =", datetime.now().strftime("%H:%M:%S %d/%m/%Y"))
  # files = [['datasets/ijcnlp_dailydialog/test/dailydialog_test.csv', "\t", 'utterance', 'emotion', "systemDailyDialogemoInstruct"]]
  # model_names = ["lzw1008/Emollama-chat-13b", "mistralai/Mistral-7B-v0.3", "lzw1008/Emollama-chat-7b"]
  # Check if there are enough arguments
  if len(sys.argv) < 5:
    print("Please provide model and task.")
    sys.exit(1)
    
    # Convert arguments to integers and sum them
    # try:
  prompt_type = str(sys.argv[1])
  domaine = str(sys.argv[2])
  task = str(sys.argv[3])
  input_data= str(sys.argv[4])
  input_dict_response = ""
  if domaine=="generateResponse":
     input_dict_response = sys.argv[5]
    #  input_dict_response = json.loads(sys.argv[6])
  elif len(sys.argv) > 5 and len(sys.argv) < 7: #can not test answer with a file
    print("Please provide text_col, label_col.")
    sys.exit(1)
  
  text_col=""
  label_col = ""
  if len(sys.argv) > 6:
    text_col = str(sys.argv[5])
    label_col = str(sys.argv[6])
  max_new_tokens = int(sys.argv[7]) if len(sys.argv)>7 else 15
  separator = str(sys.argv[8]) if len(sys.argv)>8 else "\t"
  
  accelerator = Accelerator()
  device_name = 'cuda:0' if cuda.is_available() else 'cpu'
  device = accelerator.prepare(device_name)

  print ("device_name=",device_name, input_data, text_col, label_col, task, domaine, prompt_type, max_new_tokens, str(separator))

  classify(device_name, input_data, separator, label_col, task, domaine, text_col, max_new_tokens, input_dict_response)

if __name__ == "__main__":
    main()

# exemple commandes:
# python demo_aniti.py "lzw1008/Emollama-chat-7b" "basic" "emotion" "systemMELD" "ca m'enerve pourquoi tu me dis ca a chaque fois"
# python demo_aniti.py "lzw1008/Emollama-chat-7b" "basic" "emotion" "systemMELD" "generation/in-car-conversation-dataset.tsv" "utterance" "ekman_emotion"
# python demo_aniti.py "lzw1008/Emollama-chat-7b" "basic" "intention" "intention" "il fait chaud ouvre la fenetre"
# python demo_aniti.py "lzw1008/Emollama-chat-7b" "basic" "intention" "intention" "il fait chaud ouvre la fenetre" "" "" 30