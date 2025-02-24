import './App.css';
import AudioSelection from './components/paths/audioSelection';
import EmotionRecognition from './components/paths/emotionRecognition';
import RunCommand from './components/paths/runCommand';
import SentimentAnalysis from './components/paths/sentimentAnalysis';
import SetCommand from './components/paths/setCommand';

function App() {

  return (
    <div className="App">
      <div className='main'>
        <h1>~ 𝓟𝓻𝓸𝓽𝓸𝓽𝔂𝓹𝓮 ~</h1>
        <SentimentAnalysis/>
        <SetCommand/>
        <RunCommand/>
        <AudioSelection/>
        <EmotionRecognition/>
      </div>
    </div>
  );
}

export default App;
