import './App.css';
import AudioSelection from './components/paths/audioSelection';
import EmotionRecognition from './components/paths/emotionRecognition';
import TaskSelector from './components/taskSelector';
import { useEffect, useState } from 'react';

function App() {
  const [selectedTask, setSelectedTask] = useState("emotion");
  const [loadingTask, setLoadingTask] = useState(null);

  const [audioFiles, setAudioFiles] = useState([]);
  const [selectedAudio, setSelectedAudio] = useState(null);
  
  useEffect(() => {
    const fetchAudioFiles = async () => {
      try {
        const fileList = [
          "Test_IDoNotBelieveYou.json",
          "Test_What.json",
          "Conversation.json",
          "open_window.json",
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

  return (
    <div className="App">
      <div className='main'>
        <h1>~ 𝓟𝓻𝓸𝓽𝓸𝓽𝔂𝓹𝓮 ~</h1>
        <TaskSelector
          selectedTask={selectedTask}
          setSelectedTask={setSelectedTask}
          loadingTask={loadingTask}
          setLoadingTask={setLoadingTask}
        />
        <AudioSelection
          audioFiles={audioFiles}
          setAudioFiles={setAudioFiles}
          selectedAudio={selectedAudio}
          setSelectedAudio={setSelectedAudio}
        />
        <EmotionRecognition
          selectedTask={selectedTask}
          loadingTask={loadingTask}
          audioFiles={audioFiles}
          selectedAudio={selectedAudio}
        />
      </div>
    </div>
  );
}

export default App;
