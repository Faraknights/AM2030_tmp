import './App.css';
import MicrophoneTest from './components/paths/microphoneTest';
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
        <MicrophoneTest/>
      </div>
    </div>
  );
}

export default App;
