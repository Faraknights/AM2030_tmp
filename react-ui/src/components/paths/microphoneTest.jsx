import React, { useState, useEffect, useRef } from 'react';
import Accordion from '../accordion';

const MicrophoneTest = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  useEffect(() => {
    if (isRecording) {
      startRecording();
    } else {
      stopRecording();
    }
  }, [isRecording]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        audioChunksRef.current = [];
        setAudioUrl(URL.createObjectURL(audioBlob));
      };

      mediaRecorderRef.current.start();
    } catch (error) {
      console.error('Error accessing microphone:', error);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
    }
  };

  const downloadAudio = () => {
    if (audioUrl) {
      const downloadLink = document.createElement('a');
      downloadLink.href = audioUrl;
      downloadLink.download = 'recording.wav';
      document.body.appendChild(downloadLink);
      downloadLink.click();
      document.body.removeChild(downloadLink);
    }
  };

  return (
    <Accordion
      title="Microphone Recorder"
      content={
        <>
            <span className="description">
                Allows users to record audio, play it back, and download it as a WAV file.
            </span>
            <div className="microphone-recorder">
            <button onClick={() => setIsRecording(!isRecording)}>
                {isRecording ? 'Stop Recording' : 'Start Recording'}
            </button>
            {audioUrl && (
                <div className="audio-container">
                <audio controls src={audioUrl}></audio>
                <br />
                <button className="download-button" onClick={downloadAudio}>
                    Download Recording
                </button>
                </div>
            )}
            </div>
        </>
      }
    />
  );
};

export default MicrophoneTest;
