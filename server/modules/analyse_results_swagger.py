import os
import sys
import subprocess
import locale
import warnings
import logging
import json
import base64
import io
import simpleaudio as sa
import argparse
import platform
import shutil
import uuid
from pydub import AudioSegment
from pytube import YouTube
AudioSegment.ffmpeg = r'C:\ffmpeg\bin\ffmpeg.exe'
#locale.getpreferredencoding = lambda: "UTF-8"

#Suppress all warnings
warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.CRITICAL)


def emotion_recognition_results2(results_directory, file_segment_directory, selected_file, segments_to_analyze):
    results_file_path = os.path.join(results_directory, selected_file.replace('.wav', '.json'))
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
        print(json.dumps(final_result, indent=4))
    else:
        print("Segments files missing")


def main():
    # Set up argument parser
    input_id = sys.stdin.read()
    res_dir = './results/'
    seg_dir = './segments/'

    # Construct the path to the JSON file
    json_file_path = os.path.join(res_dir, f"{input_id}.json")

    # Check if the input is a valid file
    if not os.path.isfile(json_file_path):
        print("The ID does not exist")
        return

    selected_file = os.path.basename(json_file_path)
    file_segment_directory = os.path.join(seg_dir, selected_file.replace('.wav', '/').replace('.json', '/'))
    segments_to_analyze = []
    segments_to_analyze.append('all')
    emotion_recognition_results2(res_dir, file_segment_directory, selected_file, segments_to_analyze)


if __name__ == "__main__":
    main()


