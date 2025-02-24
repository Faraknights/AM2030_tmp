import os
import sys
import time
import json
import torch
import librosa
import torchaudio
import numpy as np
import soundfile as sf
import io
import base64
import torchaudio.transforms as T
from torch import nn
from tqdm import tqdm
from pyannote.audio import Pipeline
from transformers import AutoProcessor, AutoModelForSpeechSeq2Seq
from transformers import BertTokenizer, RobertaTokenizer, BertModel, RobertaModel, AdamW, get_linear_schedule_with_warmup

device = "cuda" if torch.cuda.is_available() else "cpu"


class BERTClassifier(nn.Module):

    def __init__(self, bert_model_name, num_classes):
        super(BERTClassifier, self).__init__()
        self.bert = RobertaModel.from_pretrained(bert_model_name)
        self.dropout = nn.Dropout(0.1)
        self.fc = nn.Linear(self.bert.config.hidden_size, num_classes)

    def forward(self, input_ids, attention_mask):
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = outputs.pooler_output
        x = self.dropout(pooled_output)
        logits = self.fc(x)
        return logits


class SSLClassifier(nn.Module):

    def __init__(self, bundle, num_classes,attn_head):
        super(SSLClassifier, self).__init__()
        self.feature_extractor = bundle.get_model()
        self.num_labels = num_classes
        self.head = attn_head
        self.relu = nn.ReLU()
        num_layers=2
        hidden_dim=1024
        input_dim=1024
        output_dim = self.num_labels
        p = 0.5
        self.fc=nn.ModuleList([
            nn.Sequential(
                nn.Linear(input_dim, hidden_dim),\
                        nn.LayerNorm(hidden_dim),\
                        nn.ReLU(),\
                        nn.Dropout(p)
            )
        ])
        for lidx in range(num_layers-1):
            self.fc.append(
                nn.Sequential(
                    nn.Linear(hidden_dim, hidden_dim),\
                            nn.LayerNorm(hidden_dim),\
                            nn.ReLU(),\
                            nn.Dropout(p)
                )
            )
        self.out = nn.Sequential(
            nn.Linear(hidden_dim, output_dim)
        )
        self.inp_drop = nn.Dropout(p)

    def get_repr(self, x):
        h = self.inp_drop(x)
        for lidx, fc in enumerate(self.fc):
            h=fc(h)
        return h

    def compute_length_from_mask(self, mask):
        """
        mask: (batch_size, T)
        Assuming that the sampling rate is 16kHz, the frame shift is 20ms
        """
        wav_lens = torch.sum(mask, dim=1) # (batch_size, )
        feat_lens = torch.div(wav_lens-1, 16000*0.02, rounding_mode="floor") + 1
        feat_lens = feat_lens.int().tolist()
        return feat_lens

    # FORWARD FUNCTION FOR STATISTIC POOLING (MEAN + STD CONCAT)
    def forward(self, input_ids, mask):
        """
        Extracts features from the SSL bundle previously initialized
        and chooses the pre-defined attention head
        """
        outputs, _ = self.feature_extractor.extract_features(input_ids)
        outputs = outputs[self.head-1]

        """
        In order to do average or stat pooling, we first need to
        take in consideration the sequence length. Otherwise an
        average of the padded sequence would be done.
        """
        feat_lens = self.compute_length_from_mask(mask)
        pooled_list = []

        for input_, feat_len in zip(outputs, feat_lens):
            pooled = torch.mean(input_[:feat_len], dim=0)
            pooled_list.append(pooled)
            std = torch.std(input_[:feat_len], dim=0)


        pooled = torch.stack(pooled_list, dim=0)

        h=self.get_repr(pooled)
        outputs = self.out(h)

        return outputs


class emo_module():

    def __init__(self, model_path, speech_model_path):
        # BERT EMO TEXT MODEL INIT
        self.tokenizer = RobertaTokenizer.from_pretrained('roberta-base')
        self.model = BERTClassifier('roberta-base', num_classes=8).to(device) #Number of classes used in text emotion
        self.model.load_state_dict(torch.load(model_path, map_location=torch.device(device)))
        self.model.eval()
        # SSL EMO SPEECH MODEL INIT
        self.bundle = bundle = torchaudio.pipelines.WAVLM_LARGE
        self.speech_model = SSLClassifier(self.bundle,num_classes=8, attn_head=24) #Number of classes used in sound emotion
        self.speech_model.load_state_dict(torch.load(speech_model_path, map_location=torch.device(device)))
        self.speech_model.eval()
        self.sigmoid = nn.Sigmoid()
        self.idx_to_label = {
            0: 'ANGER (A)',
            1: 'SAD (S)',
            2: 'HAPPY (H)',
            3: 'SURPRISE (U)',
            4: 'FEAR (F)',
            5: 'DISGUST (D)',
            6: 'CONTEMPT (C)',
            7: 'NEUTRAL (N)',
            8: 'OTHER (O)',
            9: 'X (X)'
        }

    def inference(self, segment_directory, store_file, size_matters):
        start = time.time()
        labels = {
            0: 'ANGER (A)',
            1: 'SAD (S)',
            2: 'HAPPY (H)',
            3: 'SURPRISE (U)',
            4: 'FEAR (F)',
            5: 'DISGUST (D)',
            6: 'CONTEMPT (C)',
            7: 'NEUTRAL (N)'
        }
        list_of_segments = []
        os.listdir(segment_directory)
        for filename in os.listdir(segment_directory):
            file_path = os.path.join(segment_directory, filename)
            with open(file_path, 'r') as file:
                segment_dict_64 = json.load(file)
            list_of_segments.append(segment_dict_64)
        with torch.inference_mode():
            for item in list_of_segments:
                # IGNORES SEGMENTED FILES WITH LESS THAN 0.3s
                if size_matters:
                    if abs(item['end'] - item['beg']) < 0.3:
                        item['Most probable emotion (text)'] = "Segment ignored duration less than 0,3s"
                        item['Most probable emotion (text) - prob.'] = "Segment ignored duration less than 0,3s"
                        item['Probability for each emotion (text)'] = "Segment ignored  duration less than 0,3s"
                        item['Most probable emotion (speech)'] = "Segment ignored duration less than 0,3s"
                        item['Most probable emotion (speech) - prob.'] = "Segment ignored duration less than 0,3s"
                        item['Probability for each emotion (speech)'] = "Segment ignored duration less than 0,3s"
                        item['Most probable emotion (text + speech)'] = "Segment ignored duration less than 0,3s"
                        item['Most probable emotion (text + speech) - prob.'] = "Segment ignored duration less than 0,3s"
                        item['Probability for each emotion (text + speech)'] = "Segment ignored duration less than 0,3s"
                        del item['encoded_audio']
                        continue
                # TEXT BASED EMOTION PREDICTION
                encoding = self.tokenizer(item['transcription'], return_tensors='pt')
                text = encoding['input_ids'].to(device)
                mask = encoding['attention_mask'].to(device)
                pred_text = self.model(input_ids=text, attention_mask=mask)
                pred_text = self.sigmoid(pred_text)
                emo_idx = torch.argmax(pred_text, dim=1)
                emo_idx = emo_idx.cpu().numpy()[0]
                emo_text = self.idx_to_label[emo_idx]
                highest_prob = pred_text.cpu().numpy()[0][emo_idx]
                all_prob_text = pred_text.cpu().numpy()[0].tolist()
                text_results = {labels[i]: all_prob_text[i] for i in range(len(all_prob_text))}
                if 'CONTEMPT (C)' in text_results and 'DISGUST (D)' in text_results:
                    text_results['DISGUST (D)'] = text_results['CONTEMPT (C)'] if text_results['CONTEMPT (C)'] > text_results['DISGUST (D)'] else text_results['DISGUST (D)']
                    text_results.pop('CONTEMPT (C)', None)
                item['Most probable emotion (text)'] = max(text_results, key=text_results.get)
                item['Most probable emotion (text) - prob.'] = text_results[item['Most probable emotion (text)']]
                item['Probability for each emotion (text)'] = text_results
                # SPEECH BASED EMOTION PREDICTION
                encoded_audio = item['encoded_audio']
                decoded_audio = base64.b64decode(encoded_audio)
                audio_buffer = io.BytesIO(decoded_audio)
                waveform, sr = torchaudio.load(audio_buffer)
                attn_mask = np.ones(waveform.size(dim=1))
                attn_mask = torch.tensor(attn_mask)
                pred_speech = self.speech_model(waveform, attn_mask.unsqueeze(dim=0))
                pred_speech = self.sigmoid(pred_speech)
                emo_idx = torch.argmax(pred_speech, dim=1)
                emo_idx = emo_idx.cpu().numpy()[0]
                emo_speech = self.idx_to_label[emo_idx]
                highest_prob = pred_speech.cpu().numpy()[0][emo_idx]
                all_prob_speech = pred_speech.cpu().numpy()[0].tolist()
                speech_results = {labels[i]: all_prob_speech[i] for i in range(len(all_prob_speech))}
                if 'CONTEMPT (C)' in speech_results and 'DISGUST (D)' in speech_results:
                    speech_results['DISGUST (D)'] = speech_results['CONTEMPT (C)'] if speech_results['CONTEMPT (C)'] > speech_results['DISGUST (D)'] else speech_results['DISGUST (D)']
                    speech_results.pop('CONTEMPT (C)', None)
                item['Most probable emotion (speech)'] = max(speech_results, key=speech_results.get)
                item['Most probable emotion (speech) - prob.'] = speech_results[item['Most probable emotion (speech)']]
                item['Probability for each emotion (speech)'] = speech_results
                #COMBINED BASED EMOTION PREDICTION
                combined_results = {key: (text_results.get(key, 0) + speech_results.get(key, 0)) / 2 for key in text_results}
                max_value = max(combined_results.values())
                emo_combined = [key for key, value in combined_results.items() if value == max_value]
                highest_prob = max_value
                item['Most probable emotion (text + speech)'] = ", ".join(emo_combined)
                item['Most probable emotion (text + speech) - prob.'] = highest_prob
                item['Probability for each emotion (text + speech)'] = combined_results
                del item['encoded_audio']
        with open(store_file, 'w', encoding='utf-8') as f:
            sorted_list_of_segments = sorted(list_of_segments, key=lambda x: x['turn'])
            result_dic = {"Result": sorted_list_of_segments}
            json.dump(result_dic, f, indent=4)
        end = time.time()


class asr_module():

    def __init__(self,model):
        self.processor = AutoProcessor.from_pretrained(model)
        self.model = AutoModelForSpeechSeq2Seq.from_pretrained(model)

    def transcribe(self, segment_directory):
        start = time.time()
        for filename in os.listdir(segment_directory):
            file_path = os.path.join(segment_directory, filename)
            with open(file_path, 'r') as file:
                segment_dict_64 = json.load(file)
            encoded_audio = segment_dict_64['encoded_audio']
            decoded_audio = base64.b64decode(encoded_audio)
            audio_buffer = io.BytesIO(decoded_audio)
            y, sr = torchaudio.load(audio_buffer)
            if sr != 16000:
                # Resample the audio to 16000 Hz
                resampler = T.Resample(orig_freq=sr, new_freq=16000)
                y = resampler(y)

                # Update the sampling rate to 16000 Hz after resampling
                sr = 16000
            input_features = self.processor(y.numpy(), sampling_rate=sr, return_tensors="pt").input_features
            predicted_ids = self.model.generate(input_features)
            transcription = self.processor.batch_decode(
                predicted_ids,
                skip_special_tokens=True,
                task='translate',
                language='english'
            )
            segment_dict_64['transcription'] = transcription[0]
            if 'turn' not in segment_dict_64:
                segment_dict_64['turn'] = 0
            with open(file_path, 'w') as file:
                json.dump(segment_dict_64, file, indent=4)
        end = time.time()



class diarization_module():
    def __init__(self, token):
        self.pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", use_auth_token=token)
        self.pipeline = self.pipeline.to(torch.device(device))

    def segment(self, wav_file, out_dir):
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        start = time.time()
        y, sr = librosa.load(wav_file, sr=16000)
        diarization = self.pipeline(wav_file, max_speakers=3)
        itr = 0
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            beg = int(turn.start * sr)
            end = int(turn.end * sr)
            seg = y[beg:end]
            # Encode the segment to a base64 string
            buffer = io.BytesIO()
            sf.write(buffer, seg, sr, format='WAV')  # Write to buffer in WAV format
            buffer.seek(0)
            encoded_audio = base64.b64encode(buffer.read()).decode('utf-8')
            # Prepare the JSON data for this segment
            segment_data = {
                "reference": wav_file,
                "turn": itr,
                "speaker": speaker,
                "beg": turn.start,
                "end": turn.end,
                "encoded_audio": encoded_audio  # Base64-encoded audio data
            }
            fname = str(itr) + '_' + speaker + '.json'
            fname = os.path.join(out_dir, fname)
            with open(fname, 'w') as json_file:
                json.dump(segment_data, json_file, indent=4)
            itr += 1
        end = time.time()




