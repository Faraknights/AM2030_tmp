import React, { useState, useEffect, useRef } from "react";
import Accordion from "../accordion";

const AudioSelection = () => {
  const [segment, setSegment] = useState("F");
  const [audioFiles, setAudioFiles] = useState([]);
  const [isRecording, setIsRecording] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);
  const [base64Audio, setBase64Audio] = useState(null);
  const [responseMessage, setResponseMessage] = useState("");
  const [status, setStatus] = useState(null);
  console.log(segment)
  
  useEffect(() => {
    if (isRecording) {
      startRecording();
    } else {
      stopRecording();
    }
  }, [isRecording]);
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

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
        const audioUrl = URL.createObjectURL(audioBlob);
        setAudioUrl(audioUrl);
        convertToBase64(audioBlob);
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

  const convertToBase64 = (blob) => {
    const reader = new FileReader();
    reader.readAsDataURL(blob);
    reader.onloadend = () => {
      setBase64Audio(reader.result.split(',')[1]); // Remove the metadata prefix
    };
  };
  const sendAudioToBackend = async (audioData) => {
    if (audioData) {
      try {
        const requestData = {
          encoded_audio: audioData,
          ID: "",
          segment: segment,
          transcription: ""
        };

        const response = await fetch('http://localhost:5000/asr/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(requestData),
        });

        const data = await response.json();
        console.log(data)
        setResponseMessage(data.message || data.error);
        setStatus(response.status);
      } catch (error) {
        console.error("Error running command:", error);
        setResponseMessage(error.message);
        setStatus(500);
      }
    }
  };
  useEffect(() => {
    const fetchAudioFiles = async () => {
      try {
        // Manually list your JSON files
        const fileList = ["Conversation.json", "Test_IDoNotBelieveYou.json", "Test_What.json"];

        const fileDataPromises = fileList.map(async (fileName) => {
          const fileResponse = await fetch(`/audioSamples/${fileName}`);
          const fileData = await fileResponse.json();

          return {
            name: fileName,
            audioUrl: `data:audio/wav;base64,${fileData.encoded_audio}`,
            base64: fileData.encoded_audio
          };
        });

        const files = await Promise.all(fileDataPromises);
        setAudioFiles(files);
      } catch (error) {
        console.error("Error fetching audio files:", error);
      }
    };

    fetchAudioFiles();
  }, []);

  return (
    <Accordion
      title="Audio selection"
      content={
        <div className="audio-list">
					<span className="description">
          allows users to record audio, select preloaded audio files, and send them to a backend for later processings.
					</span>
          <input type="checkbox" value={segment === "T"} onClick={() => setSegment(segment === "T" ? "F" : "T")}/>          
          <span> - Segment text ?</span>
          <div className="separation"></div>
          {audioFiles.map((file, index) => (
            <div key={index} className="audio-row">
              <span className="audio-name">{file.name}</span>
              <audio controls src={file.audioUrl}></audio>
              <button onClick={() => sendAudioToBackend(file.base64)}>
                Send Audio to Backend
              </button>
            </div>
          ))}
          <div className="separation"></div>
          <div className="audio-row">
            <button onClick={() => setIsRecording(!isRecording)}>
              {isRecording ? 'Stop Recording' : 'Start Recording'}
            </button>
            {audioUrl && (
              <>
                <audio controls src={audioUrl}></audio>
                <button onClick={() => sendAudioToBackend(base64Audio)}>
                  Send Audio to Backend
                </button>
              </>
            )}
          </div>
					{responseMessage && (
						<>
							<span className="resultTitle">Status: {status}</span>
							<div className={`result ${status === 200 ? "success" : "fail"}`}>
								<div>{responseMessage}</div>
							</div>
						</>
					)}
        </div>
      }
    />
  );
};

export default AudioSelection;
