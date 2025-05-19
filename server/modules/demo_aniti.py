import json
import os
import re
from datetime import datetime
import warnings
import gc

from torch import cuda
from llama_cpp import Llama

warnings.filterwarnings('ignore')

# Memory cleanup......................................................................................
gc.collect()


#Check if the Llama.cpp got compiled with the GPU well................................................

from llama_cpp.llama_cpp import load_shared_library
import pathlib

def is_gpu_available_v3() -> bool:
    lib = load_shared_library('llama',pathlib.Path('/usr/local/lib/python3.10/dist-packages/llama_cpp/lib'))
    return bool(lib.llama_supports_gpu_offload())
print("[DEBUG] - ", is_gpu_available_v3())

#Loading the model ....................................................................................

print("[INFO]", datetime.now().strftime("[%Y-%m-%d %H:%M:%S]"), "Loading trained model...")
device_name = 'cuda:0' if cuda.is_available() else 'cpu'

model_path = "/models/Emollama-7b.i1-Q4_K_M.gguf"

model = Llama(
    model_path=model_path,
    n_ctx=1024,
    n_gpu_layers=50,
    n_batch=16
)
print("[INFO]", datetime.now().strftime("[%Y-%m-%d %H:%M:%S]"), "Model loaded successfully.")

#Actual stuff...........................................................................................
def load_prompt(file_name, folder="server/modules/prompts/"):
    file_path = os.path.join(folder, f"{file_name}.txt")
    print(file_path)
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: The prompt file '{file_name}.txt' does not exist.")
        return None
    
def format_conversation(user_text , task, domaine, input_dict_response=None):
    print("debug=", user_text , "task=", task, "domaine=", domaine, "input_dict_response=", input_dict_response)

    task_prompt = load_prompt(task)

    if not task_prompt:
        raise FileNotFoundError(f"Missing prompt file: task={task}, user_text={user_text}")

    return task_prompt.replace("{USER_TEXT}", user_text)

def extract_intention(response):
    match = re.search(r"\b(\w+)\s*-\s*(\w+)\b", response)
    return f"{match.group(1)}-{match.group(2)}" if match else None

def extract_label_or_text(text, domaine, fr=True):
    if "generateResponse" in domaine:
        assistant_label = "<|im_start|> assistant"
        index = text.find(assistant_label)
        text = text[index + len(assistant_label):]
        return text
    
    if domaine == "intention":
        assistant_label = "the format verb-action_name is"
        index = text.find(assistant_label)
        text = text[index + len(assistant_label):]
        return extract_intention(text)
    
    labels_dic = {
        "emotion": {
            "neutral": {"neutre", "neutral"},
            "joy": {"joie", "joy"},
            "anger": {"colere", "colère", "anger"},
            "surprise": {"surprise"},
            "sadness": {"tristesse", "sadness"},
            "disgust": {"degout", "dégoût", "disgust"},
            "fear": {"peur", "fear"}
        }
    }

    text_lower = text.lower()

    for label, synonyms in labels_dic["emotion"].items():
        for synonym in synonyms:
            if synonym in text_lower:
                return label

    return f"No classification: neutral:: {text}"

def classify(user_sentence, task, domaine, input_dict_response):

    prompt = format_conversation(user_sentence, task, domaine, input_dict_response)

    output = model(prompt, max_tokens=512, temperature=0.7)["choices"][0]["text"]

    classification = extract_label_or_text(output, domaine)

    return classification

#The function that gets call externally.....................................................................
def run_classification(domaine: str, task: str, input_data: str, input_dict_response: str = ""):

    gc.collect()

    if domaine != "generateResponse" and not (input_data and task):
        raise ValueError("For classification tasks, input_data and task must be provided.")
    
    if domaine == "generateResponse" and not input_dict_response:
        raise ValueError("For 'generateResponse' domaine, input_dict_response must be provided.")

    return classify(input_data, task, domaine, input_dict_response)

# exemple commandes:
# python demo_aniti.py "lzw1008/Emollama-chat-7b" "basic" "emotion" "systemMELD" "ca m'enerve pourquoi tu me dis ca a chaque fois"
# python demo_aniti.py "lzw1008/Emollama-chat-7b" "basic" "emotion" "systemMELD" "generation/in-car-conversation-dataset.tsv" "utterance" "ekman_emotion"
# python demo_aniti.py "lzw1008/Emollama-chat-7b" "basic" "intention" "intention" "il fait chaud ouvre la fenetre"
# python demo_aniti.py "lzw1008/Emollama-chat-7b" "basic" "intention" "intention" "il fait chaud ouvre la fenetre" "" "" 30