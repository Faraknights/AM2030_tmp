import os
import subprocess
import warnings
import logging
import json
import base64
import platform
import uuid
from pydub import AudioSegment
AudioSegment.ffmpeg = r'C:\ffmpeg\bin\ffmpeg.exe'
#locale.getpreferredencoding = lambda: "UTF-8"
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Suppress all warnings
warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.CRITICAL)


def segmentation_of_data_True(segments_directory, input_file):
    selected_file = os.path.basename(input_file)
    selected_file_path = input_file
    file_segments_directory = os.path.join(segments_directory, selected_file.replace('.wav', '/').replace('.json', '/'))
    if not os.path.exists(file_segments_directory):
        os.makedirs(file_segments_directory)
    token = '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'  # HuggingFace authentication token (used for pyannote 3.1)
    from ER_functions_swagger import diarization_module  # Imports the diarization module
    diarization = diarization_module(token)  # Responsible for identifying the speakers and when they speak.
    diarization.segment(selected_file_path, file_segments_directory)
    from ER_functions_swagger import asr_module  # Import the asr_module
    asr = asr_module("openai/whisper-small")  # Responsible for Speech to text
    asr.transcribe(file_segments_directory)
    size_matters = True
    return file_segments_directory, selected_file, size_matters


def segmentation_of_data_False(segments_directory, input_file):
    selected_file = os.path.basename(input_file)
    selected_file_path_json = input_file
    file_segments_directory = os.path.join(segments_directory, selected_file.replace('.wav', '/').replace('.json', '/'))
    if not os.path.exists(file_segments_directory):
        os.makedirs(file_segments_directory)
    fname = os.path.join(file_segments_directory, selected_file)
    with open(selected_file_path_json, 'r') as file:
        segment_dic = json.load(file)
    if not segment_dic['transcription']:
        from ER_functions_swagger import asr_module  # Import the asr_module
        with open(fname, 'w') as json_file:
            json.dump(segment_dic, json_file, indent=4)
        asr = asr_module("openai/whisper-small")  # Responsible for Speech to text
        asr.transcribe(file_segments_directory)

    else:
        segment_dic['turn'] = 0
        with open(fname, 'w') as json_file:
            json.dump(segment_dic, json_file, indent=4)
    size_matters = False
    return file_segments_directory, selected_file, size_matters


def emotion_recognition_results(results_directory, file_segment_directory, selected_file, text_classifier, speech_classifier, size_matters, segments_to_analyze):
    results_file_path = os.path.join(results_directory, selected_file.replace('.wav', '.json'))
    from ER_functions_swagger import emo_module
    emo = emo_module(text_classifier, speech_classifier)
    emo.inference(file_segment_directory, results_file_path, size_matters)
    segment_directory_dic = []
    for filename in os.listdir(file_segment_directory):
        file_path = os.path.join(file_segment_directory, filename)
        if os.path.isfile(file_path) and filename.endswith('.json'):
            with open(file_path, 'r') as file:
                data_dic = json.load(file)
                data_dic['filename'] = filename
                segment_directory_dic.append(data_dic)
    segment_directory_dic.sort(key=lambda x: x.get('turn', 0))
    all_segment_files = [data['filename'] for data in segment_directory_dic]
    with open(results_file_path, 'r') as file:
        results_list = json.load(file)
        results_list = results_list["Result"]
    if all_segment_files:
        selection_dic = {}
        for i, file in enumerate(all_segment_files, 0):
            selection_dic[i] = file
        possible_indexes = list(selection_dic.keys())
        if 'all' in segments_to_analyze:
            segments_to_analyze = list(possible_indexes)
        else:
            segments_to_analyze = sorted(set(possible_indexes) & set(segments_to_analyze))
        final_result = {"Result": []}
        for i in segments_to_analyze:
            result_i = {}
            choice_segment = i
            selected_segment = selection_dic[choice_segment]
            segment_dic = [d for d in segment_directory_dic if d.get('filename') == selected_segment]


            turn_to_analyse = segment_dic[0]['turn']
            segment_result_dic = [d for d in results_list if d.get('turn') == turn_to_analyse]
            segment_audio = segment_dic[0]['encoded_audio']
            segment_transcription = segment_dic[0]['transcription']
            segment_emotion_text = segment_result_dic[0]['Most probable emotion (text)']
            segment_emotion_speech = segment_result_dic[0]['Most probable emotion (speech)']
            segment_emotion = segment_result_dic[0]['Most probable emotion (text + speech)']

            result_i["Transcription"] = segment_transcription
            result_i["Emotion (text)"] = segment_emotion_text
            result_i["Emotion (speech)"] = segment_emotion_speech
            result_i["Emotion (text + speech)"] = segment_emotion
            final_result["Result"].append(result_i)
        return json.dumps(final_result, indent=4)
    else:
        return 'Segments files missing'



def analyze_emotion(data_file):
    # Ensure that the JSON file has the required key `encoded_audio`
    if 'encoded_audio' not in data_file:
        return "Required key encoded audio missing"

    if 'transcription' not in data_file or not data_file['transcription']:
        data_file['transcription'] = ""  # Assign empty string if missing or empty

    if 'segment' not in data_file or not data_file['segment']:
        data_file['segment'] = "F"  # Assign empty string if missing or empty

    if 'ID' not in data_file or not data_file['ID']:
        data_file['ID'] = str(uuid.uuid4())  # Assign a new GUID if missing or empty

    # Set the necessary directories
    if not os.path.exists('./ckpts'):
        os.makedirs('./ckpts')
    required_files = ["bert_classifier.pth", "exp6_results_slurm.pth"]
    missing_files = [f for f in required_files if not os.path.exists(os.path.join('./ckpts', f))]
    if missing_files:
        # If any files are missing, use gdown to download them
        if 'bert_classifier.pth' in missing_files:
            subprocess.run(['gdown', '1RafePeKexhfyJBNGm10JyBQPSFyNi_Jd'], check=True)
        if 'exp6_results_slurm.pth' in missing_files:
            subprocess.run(['gdown', '15V2D-eDcrYIpun7MtYZS2BA3XJUvTy3x'], check=True)
        # Move downloaded files (assuming they are named as required_files)
        if platform.system() == 'Windows':
            # On Windows, use the 'move' command with wildcard
            subprocess.run(['move', '*.pth', './ckpts'], shell=True, check=True)
        else:
            # On Linux/macOS, use 'mv' with wildcard
            subprocess.run(['mv', '*.pth', './ckpts'], check=True)
    text_classifier_path = './ckpts/bert_classifier.pth'
    speech_classifier_path = './ckpts/exp6_results_slurm.pth'
    if not os.path.exists('./data'):
        os.makedirs('./data')
    data_dir = './data/'
    if not os.path.exists('./segments'):
        os.makedirs('./segments')
    seg_dir = './segments/'
    if not os.path.exists('./results'):
        os.makedirs('./results')
    res_dir = './results/'

    # Create a new directory inside ./data/ with the ID as its name
    id_dir = os.path.join(data_dir, data_file['ID'])
    if not os.path.exists(id_dir):
        os.makedirs(id_dir)

    # Save the data_file variable as a JSON file inside the new directory
    data_file_path = os.path.join(id_dir, f"{data_file['ID']}.json")
    with open(data_file_path, 'w') as json_file:
        json.dump(data_file, json_file, indent=4)

    # Save the encoded audio (assuming it's base64 encoded) as a .wav file inside the same directory
    encoded_audio = data_file['encoded_audio']
    audio_data = base64.b64decode(encoded_audio)  # Decode the base64-encoded audio

    audio_file_path = os.path.join(id_dir, f"{data_file['ID']}.wav")
    with open(audio_file_path, 'wb') as audio_file:
        audio_file.write(audio_data)

    if data_file['segment'] == "T":
        input_file = audio_file_path
        [file_segment_directory, selected_file, size_matters] = segmentation_of_data_True(seg_dir, input_file)
        segments_to_analyze = []
        segments_to_analyze.append('all')
        return emotion_recognition_results(res_dir, file_segment_directory, selected_file, text_classifier_path, speech_classifier_path, size_matters, segments_to_analyze)

    elif data_file['segment'] == "F":
        input_file = data_file_path
        [file_segment_directory, selected_file, size_matters] = segmentation_of_data_False(seg_dir, input_file)
        segments_to_analyze = []
        segments_to_analyze.append('all')
        return emotion_recognition_results(res_dir, file_segment_directory, selected_file, text_classifier_path, speech_classifier_path, size_matters, segments_to_analyze)


