import React, { useState } from "react";
import Accordion from "../accordion";

const EmotionRecognition = ({ selectedTask, loadingTask, audioFiles, selectedAudio }) => {
	if (audioFiles && selectedAudio != null && audioFiles[selectedAudio]) {
		console.log(audioFiles[selectedAudio].transcription)
	  }
	const isModelPreparing = loadingTask === selectedTask;
	const [responseMessage, setResponseMessage] = useState([]);
	const [status, setStatus] = useState(null);
	const [isLoading, setIsLoading] = useState(false);

	const handleRunCommand = async () => {
		setResponseMessage([]);
		if (!audioFiles || selectedAudio == null || !audioFiles[selectedAudio]) {
		  setResponseMessage([{ text: "No audio transcription available.", output: "" }]);
		  setStatus(400);
		  return;
		}
	  
		setIsLoading(true);
		try {
		  const { transcription, segment } = audioFiles[selectedAudio];
	  
		  // If segment mode is "T", split into sentences and send requests for each
		  if (segment === "T") {
			const sentences = transcription.split(/[.,!?]/).map(s => s.trim()).filter(Boolean);
	  
			const results = [];
			for (const sentence of sentences) {
				console.log(sentence, sentences)
			  const response = await fetch("http://localhost:5000/asr/emotion", {
				method: "POST",
				headers: {
				  "Content-Type": "application/json",
				},
				body: JSON.stringify({ transcription: sentence.trim(), task: selectedTask }),
			  });
	  
			  const data = await response.json();
			  results.push({
				text: sentence.trim(),
				output: data.result || data.error || "No result received",
			  });
			  setResponseMessage(results)
	  
			  setStatus(response.status);
			}
		  } else {
			// Default behavior if no segmentation
			const response = await fetch("http://localhost:5000/asr/emotion", {
			  method: "POST",
			  headers: {
				"Content-Type": "application/json",
			  },
			  body: JSON.stringify({ transcription, task: selectedTask }),
			});
	  
			const data = await response.json();
			setResponseMessage([
			  { text: transcription, output: data.result || data.error || "No result received" },
			]);
			setStatus(response.status);
		  }
		} catch (error) {
		  console.error("Error running command:", error);
		  setResponseMessage([{ text: "Error", output: error.message }]);
		  setStatus(500);
		} finally {
		  setIsLoading(false);
		}
	  };
	  
	return (
		<Accordion
			title={"Emotion Recognition"}
			content={
				<div id="runCommand">
					<span className="description">
						<span>
							This module will recognize the emotion in the audio sent through the module <strong>[Audio Selection]</strong>. It will first segment if asked, then transcribe the text before analyzing the emotion in the voice and the text, combining probabilities to get a final decision on the emotion.
						</span>
					</span>
					<button 
						className={`execute ${isLoading || isModelPreparing ? "disabled" : ""}`} 
						onClick={handleRunCommand} 
						disabled={isLoading || isModelPreparing}
					>
						{isLoading ? "Running..." : (isModelPreparing ? 'Preparing the model...' :"Recognize the emotion")}
					</button>
					{responseMessage && (
						<>
							<span className="resultTitle">Status: {status}</span>
							<div className={`result ${status === 200 ? "success" : "fail"}`}>
								{responseMessage.map((response, index) => (
									<div key={index}>
										<span>{response.text}</span>
										<span>{response.output}</span>
									</div>
								))}
							</div>
						</>
					)}
				</div>
			}
		/>
	);
};

export default EmotionRecognition;
