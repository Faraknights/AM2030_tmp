import React, { useEffect, useRef, useState } from "react";
import Accordion from "../accordion";



const EmotionRecognition = ({ selectedTask, loadingTask, audioFiles, selectedAudio }) => {
	if (audioFiles && selectedAudio != null && audioFiles[selectedAudio]) {
		console.log(audioFiles[selectedAudio].transcription)
	  }
	const isModelPreparing = loadingTask === selectedTask;
	const [responseMessage, setResponseMessage] = useState([]);
	const [status, setStatus] = useState(null);
	const [isLoading, setIsLoading] = useState(false);

	const resultRef = useRef(null);

	const taskLabels = {
		emotion: {
			title: "Emotion Recognition",
			description: "recognize the user's emotion",
			full: "This module will recognize the emotion in the audio sent through the module [Audio Selection]. It will first segment if asked, then transcribe the text before analyzing the emotion in the voice and the text, combining probabilities to get a final decision.",
			button: "Recognize the emotion"
		},
		intention: {
			title: "Intention Detection",
			description: "detect the user's intention",
			full: "This module will detect the user's intention in the audio sent through the module [Audio Selection]. It will first segment if needed, then transcribe the text before analyzing the utterance to extract the explicit action requested by the driver, in the form verb-topic (e.g., play-music, start-navigation).",
			button: "Detect the intention"
		}
	};
	
	const currentLabels = taskLabels[selectedTask] || {
		title: "Recognition",
		description: "analyze the selected audio",
		full: "This module will analyze the audio sent through the module [Audio Selection].",
		button: "Run analysis"
	};

	useEffect(() => {
		if (resultRef.current) {
			resultRef.current.scrollTop = resultRef.current.scrollHeight;
		}
	}, [responseMessage]);
	

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
	  
			for (const sentence of sentences) {
				const response = await fetch("http://localhost:5000/asr/emotion", {
				  method: "POST",
				  headers: {
					"Content-Type": "application/json",
				  },
				  body: JSON.stringify({ transcription: sentence.trim(), task: selectedTask }),
				});
			  
				const data = await response.json();
				const newResult = {
				  text: sentence.trim(),
				  output: data.result || data.error || "No result received",
				};
			  
				setResponseMessage(prev => [...prev, newResult]);
			  
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

	const noAudioSelected = selectedAudio == null;
	const isTranscriptionEmpty = !noAudioSelected &&
								 (!audioFiles ||
									!audioFiles[selectedAudio] ||
									!audioFiles[selectedAudio].transcription ||
									audioFiles[selectedAudio].transcription.trim() === "");

	return (
		<Accordion
			title={currentLabels.title}
			content={
				<div id="runCommand">
					<span className="description">
						<span>{currentLabels.full}</span>
					</span>
					{noAudioSelected && (<span className="warning">⚠ Warning: You must select an audio file.</span>)}
					{isTranscriptionEmpty && (<span className="warning">⚠ Warning: The selected audio must have a full transcription to be sent to the model.</span>)}
					<button
						className={`execute ${
							selectedTask == null ||
							isLoading ||
							isModelPreparing ||
							noAudioSelected ||
							isTranscriptionEmpty
							? "disabled"
							: ""
						}`}
						onClick={handleRunCommand}
						disabled={
							selectedTask == null ||
							isLoading ||
							isModelPreparing ||
							noAudioSelected ||
							isTranscriptionEmpty
						}
					>
						{isLoading
							? "Running..."
							: isModelPreparing
							? "Preparing the model..."
							: currentLabels.button}
					</button>
			
					{responseMessage.length > 0 && (
						<>
							<span className="resultTitle">Status: {status}</span>
							<div
								ref={resultRef}
								className={`result ${status === 200 ? "success" : "fail"}`}
							>
								{responseMessage.map((response, index) => (
									<div key={index}>
										<span className={response.text === "Error" ? "error" : ""}>
											{response.text}
										</span>
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
}

export default EmotionRecognition;
