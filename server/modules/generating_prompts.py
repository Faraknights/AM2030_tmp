import os
import wexpect
import time

def process_txt_prompts_and_save_single_file(input_folder):
    for filename in os.listdir(input_folder):
        if filename.endswith(".txt"):
            txt_path = os.path.join(input_folder, filename)
            with open(txt_path, "r", encoding="utf-8") as f:
                prompt_text = f.read().strip()

            print(f"Processing {filename}...")
            
            flat_prompt = prompt_text.replace('\n', '\\n')

            child = wexpect.spawn('ollama run llama3:8b')
            child.expect('>')

            child.sendline(flat_prompt)
            child.expect('>')

            tmp = f'/save {filename[:-4]}'
            print(tmp)
            child.sendline(tmp)
            child.expect('>')

            child.sendline('\x04') 
            child.expect(wexpect.EOF)

# setup chemin
base_dir = os.path.dirname(os.path.abspath(__file__))
input_folder = os.path.join(base_dir, "conversation_raw_prompts")

process_txt_prompts_and_save_single_file(input_folder)
