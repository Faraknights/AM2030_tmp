import React, { useState } from "react";
import Accordion from "../accordion";

const EmotionRecognition = () => {
	const [responseMessage, setResponseMessage] = useState("");
	const [status, setStatus] = useState(null);
	const [isLoading, setIsLoading] = useState(false);

	const handleRunCommand = async () => {
		setIsLoading(true);
		try {
			const response = await fetch("http://localhost:5000/asr/emotion", {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
			});
			const data = await response.json();
			console.log(data);
			setResponseMessage(data.emotion || data.error);
			setStatus(response.status);
		} catch (error) {
			console.error("Error running command:", error);
			setResponseMessage(error.message);
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
						<br />
						<span className="note" style={{ color: "red", fontStyle: "italic" }}>
							Be aware that the first time this module is run, it will take more time as it needs to download <strong>Bert_classifier.pth</strong> and <strong>exp6_results_slurm.pth</strong>, which are ~1.5GB.
						</span>
					</span>
					<button 
						className={`execute ${isLoading ? "disabled" : ""}`} 
						onClick={handleRunCommand} 
						disabled={isLoading}
					>
						{isLoading ? "Running..." : "Recognize the emotion"}
					</button>
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

export default EmotionRecognition;
