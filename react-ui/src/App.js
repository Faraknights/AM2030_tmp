import './App.css';
import AudioSelection from './components/paths/audioSelection';
import EmotionRecognition from './components/paths/emotionRecognition';

function App() {

  return (
    <div className="App">
      <div className='main'>
        <h1>~ 𝓟𝓻𝓸𝓽𝓸𝓽𝔂𝓹𝓮 ~</h1>
        <AudioSelection/>
        <EmotionRecognition/>
      </div>
    </div>
  );
}

export default App;
