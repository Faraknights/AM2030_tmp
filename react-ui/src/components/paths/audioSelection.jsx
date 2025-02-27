import React, { useState, useEffect, useRef } from "react";
import Accordion from "../accordion";
import TextInput from "../textInput";
import SelectInput from "../selectInput";

const AudioSelection = () => {
  const [audioFiles, setAudioFiles] = useState([]);
  const [isRecording, setIsRecording] = useState(false);
  const [responseMessage, setResponseMessage] = useState("");
  const [status, setStatus] = useState(null);
  const [disabledButton, setDisabledButton] = useState(null);

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
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/wav" });
        audioChunksRef.current = [];
        const audioUrl = URL.createObjectURL(audioBlob);

        const reader = new FileReader();
        reader.readAsDataURL(audioBlob);
        reader.onloadend = () => {
          const base64 = reader.result.split(",")[1];

          setAudioFiles((prevFiles) => [
            ...prevFiles,
            {
              ID: `Recorded_${prevFiles.length + 1}`,
              encoded_audio: base64,
              audioUrl: audioUrl,
              segment: "F",
              transcription: "", 
            },
          ]);
        };
      };

      mediaRecorderRef.current.start();
    } catch (error) {
      console.error("Error accessing microphone:", error);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
    }
  };

  useEffect(() => {
    if (isRecording) {
      startRecording();
    } else {
      stopRecording();
    }
  }, [isRecording]);

  const updateAudioFileID = (index, newID) => {
    setAudioFiles((prevFiles) => {
      const updatedFiles = [...prevFiles];
      updatedFiles[index] = { ...updatedFiles[index], ID: newID };
      return updatedFiles;
    });
  };

  const updateAudioFileSegment = (index, newSegment) => {
    setAudioFiles((prevFiles) => {
      const updatedFiles = [...prevFiles];
      updatedFiles[index] = { ...updatedFiles[index], segment: newSegment };
      return updatedFiles;
    });
  };

  const updateAudioFileTranscription = (index, newTranscription) => {
    setAudioFiles((prevFiles) => {
      const updatedFiles = [...prevFiles];
      updatedFiles[index] = { ...updatedFiles[index], transcription: newTranscription };
      return updatedFiles;
    });
  };

  const sendAudioToBackend = async (audioData, index) => {
    if (audioData) {
      try {
        setDisabledButton(index);
        const requestData = {
          encoded_audio: audioData.encoded_audio,
          ID: audioData.ID,
          segment: audioData.segment,
          transcription: audioData.transcription, 
        };

        const response = await fetch("http://localhost:5000/asr/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(requestData),
        });

        const data = await response.json();
        setResponseMessage(data.message || data.error);
        setStatus(response.status);
      } catch (error) {
        console.error("Error running command:", error);
        setResponseMessage(error.message);
        setStatus(500);
      }
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];

    if (file) {
      const fileReader = new FileReader();

      fileReader.onloadend = async () => {
        const fileContent = fileReader.result;

        if (file.name.endsWith(".json")) {
          try {
            const jsonData = JSON.parse(fileContent);
            setAudioFiles((prevFiles) => [
              ...prevFiles,
              {
                ID: jsonData.ID,
                encoded_audio: jsonData.encoded_audio,
                audioUrl: `data:audio/wav;base64,${jsonData.encoded_audio}`,
                segment: jsonData.segment || "F",
                transcription: jsonData.transcription || "", 
              },
            ]);
          } catch (error) {
            console.error("Error parsing JSON:", error);
          }
        } else if (file.name.endsWith(".wav")) {
          const arrayBuffer = await file.arrayBuffer();
          const audioBlob = new Blob([arrayBuffer], { type: "audio/wav" });
          const audioUrl = URL.createObjectURL(audioBlob);

          const reader = new FileReader();
          reader.readAsDataURL(audioBlob);
          reader.onloadend = () => {
            const base64 = reader.result.split(",")[1];
            const fileNameWithoutExtension = file.name.replace(/\.[^/.]+$/, "");

            setAudioFiles((prevFiles) => [
              ...prevFiles,
              {
                ID: fileNameWithoutExtension,
                encoded_audio: base64,
                audioUrl: audioUrl,
                segment: "F",
                transcription: "", 
              },
            ]);
          };
        } else {
          alert("Please upload a valid .wav or .json file.");
        }
      };

      fileReader.readAsText(file);
    }
  };

  useEffect(() => {
    const fetchAudioFiles = async () => {
      try {
        const fileList = [
          "Test_IDoNotBelieveYou.json",
          "Test_What.json",
          "Conversation.json",
        ];

        const fileDataPromises = fileList.map(async (fileName) => {
          const fileResponse = await fetch(`/audioSamples/${fileName}`);
          const fileData = await fileResponse.json();

          return {
            ID: fileData.ID,
            encoded_audio: fileData.encoded_audio,
            audioUrl: `data:audio/wav;base64,${fileData.encoded_audio}`,
            segment: fileData.segment || "F",
            transcription: fileData.transcription || "",
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

  const downloadWavFile = (audioData) => {
    const audioBlob = new Blob([new Uint8Array(atob(audioData.encoded_audio).split("").map(c => c.charCodeAt(0)))], { type: "audio/wav" });
    const url = URL.createObjectURL(audioBlob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${audioData.ID}.wav`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const downloadJsonFile = (audioData) => {
    const jsonData = JSON.stringify(audioData);
    const blob = new Blob([jsonData], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${audioData.ID}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Accordion
      title="Audio selection"
      content={
        <div className="audio-list">
          <span className="description">
          Allows users to record audio, select preloaded audio files, upload new files in .wav or .json format, and send them to a backend for later processing. It also allows users to download the files in .wav or .json format.
          </span>
          {audioFiles.map((file, index) => (
            <>
              <div key={index} className="audio-row">
                <span className="number">{index + 1}.</span>
                <TextInput
                  value={file.ID}
                  setValue={(newID) => updateAudioFileID(index, newID)}
                  placeholder="Audio ID"
                  hasError={file.ID === ""}
                />
                <SelectInput
                  value={file.segment}
                  setValue={(newSegment) => updateAudioFileSegment(index, newSegment)}
                  placeholder="Segment"
                  options={[
                    { value: 'F', text: 'False' },
                    { value: 'T', text: 'True' }
                  ]}
                />
                <audio controls src={file.audioUrl}></audio>
                <button
                  onClick={() => sendAudioToBackend(file, index)}
                  className={`sendAudioButton ${disabledButton === index ? "disabled" : ""}`}
                >
                  {disabledButton === index ? "Audio sent" : "Send Audio to Backend"}
                </button>
                <button className="download" title="Download JSON file" onClick={() => downloadJsonFile(file)}>
                  <svg width="20" height="20" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" className="icon">
                    <polyline points="8 12 12 16 16 12" fill="none" stroke="black" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1" />
                    <path d="M5 21H19M12 3V16" fill="none" stroke="black" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1" />
                  </svg>
                  <span>.json</span>
                </button>

                <button className="download" title="Download .wav file" onClick={() => downloadWavFile(file)}>
                  <svg width="20" height="20" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" className="icon">
                    <polyline points="8 12 12 16 16 12" fill="none" stroke="black" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1" />
                    <path d="M5 21H19M12 3V16" fill="none" stroke="black" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1" />
                  </svg>
                  <span>.wav</span>
                </button>
                <TextInput
                  className={"transcript " + (file.segment === "T" ? "disabled" : "")}
                  value={file.segment === "T" ? "" : file.transcription}
                  setValue={(newTranscription) => updateAudioFileTranscription(index, newTranscription)}
                  placeholder="Transcription"
                />
                <div className="vertical"><div></div></div>
              </div>
            </>
          ))}
          <div className="separation"></div>
          <div className="horizontal">
            <button className={`recordingButton ${isRecording ? "recording" : ""}`} onClick={() => setIsRecording(!isRecording)}>
              {isRecording ? "Stop Recording" : "Start Recording"}
            </button>
            <label className="uploadButton">
              <span>Upload a json/wav file</span>
              <input
                type="file"
                accept=".wav,.json"
                onChange={handleFileUpload}
                className="upload"
              />
            </label>
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
