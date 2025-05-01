import os
import sys
import re
import csv
from datetime import datetime
import warnings
import gc

import pandas as pd
from datasets import Dataset
from sklearn.metrics import classification_report
from torch import cuda
from transformers import GenerationConfig, LlamaTokenizer
from accelerate import Accelerator
from llama_cpp import Llama

warnings.filterwarnings('ignore')

# Memory cleanup
gc.collect()

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

def load_prompt(file_name, folder="server/modules/prompts/"):
    file_path = os.path.join(folder, f"{file_name}.txt")
    print(file_path)
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: The prompt file '{file_name}.txt' does not exist.")
        return None

def format_conversation(row, label_col, text_col, task, domaine, input_dict_response=None):
    print("debug=", row, label_col, text_col, "task=", task, "domaine=", domaine, "input_dict_response=", input_dict_response)

    prompt_template = load_prompt("system")
    user_text = load_prompt("userGenerate") if "generateResponse" in task else load_prompt("user")

    if not prompt_template or not user_text:
        return {"error": "Prompt template or user text could not be loaded."}

    if isinstance(row, str):
        if "generateResponse" in task:
            prompt_tmp = load_prompt(task).format(input_dict_response=input_dict_response) if load_prompt(task) else ""
        else:
            prompt_tmp = load_prompt(task)
        
        return prompt_template.format(
            prompt_task=prompt_tmp,
            user_text=user_text.format(label=domaine) + "['\\begin_text']" + row + "['\\end_text']",
            call_for_action=domaine,
            answer=""
        )
    
    prompt = prompt_template.format(
        prompt_task=load_prompt(task),
        user_text=user_text.format(label=domaine) + "['\\begin_text']" + row[text_col] + "['\\end_text']",
        call_for_action=domaine,
        answer=row[label_col] + "<|im_end|>" if label_col else ""
    )
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
  try:
    print("[INFO]", datetime.now().strftime("[%Y-%m-%d %H:%M:%S]"), "Loading trained model...")

    model_path = "/models/Emollama-7b.i1-Q4_K_M.gguf"

    model = Llama(
        model_path=model_path,
        n_ctx=2048,
        n_batch=1,
        device=device_name
    )

    print("[INFO]", datetime.now().strftime("[%Y-%m-%d %H:%M:%S]"), "Model loaded successfully.")

    prompt = format_conversation(file_test, False, False, task, domaine, input_dict_response)
    print("[DEBUG] Prompt sample:", prompt[:200], "..." if len(prompt) > 200 else "")

    tokens = model.tokenize(prompt.encode('utf-8'))
    print("[DEBUG] Tokenized input length:", len(tokens))

    generated_tokens = model.generate(tokens=tokens)

    print("[INFO]", datetime.now().strftime("[%Y-%m-%d %H:%M:%S]"), "Decoding output...")

    generated_text = model.detokenize(generated_tokens)

    classification = extract_label_or_text(generated_text, task, domaine)

    print("[RESULT]", classification)
    print("[INFO]", datetime.now().strftime("[%Y-%m-%d %H:%M:%S]"), "\n---------------------------------")

    return classification

  except Exception as e:
    print("[ERROR]", datetime.now().strftime("[%Y-%m-%d %H:%M:%S]"), f"An error occurred: {e}")
    return None

def main():
  gc.collect()
  print(len(sys.argv), "Begin: Current Time =", datetime.now().strftime("%H:%M:%S %d/%m/%Y"))

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
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exc()

# exemple commandes:
# python demo_aniti.py "lzw1008/Emollama-chat-7b" "basic" "emotion" "systemMELD" "ca m'enerve pourquoi tu me dis ca a chaque fois"
# python demo_aniti.py "lzw1008/Emollama-chat-7b" "basic" "emotion" "systemMELD" "generation/in-car-conversation-dataset.tsv" "utterance" "ekman_emotion"
# python demo_aniti.py "lzw1008/Emollama-chat-7b" "basic" "intention" "intention" "il fait chaud ouvre la fenetre"
# python demo_aniti.py "lzw1008/Emollama-chat-7b" "basic" "intention" "intention" "il fait chaud ouvre la fenetre" "" "" 30