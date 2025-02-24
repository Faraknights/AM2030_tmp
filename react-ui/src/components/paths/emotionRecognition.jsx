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
			title={"Run Command"}
			content={
				<div id="runCommand">
					<span className="description">
						Provide parameter values to execute the command.
					</span>
					<button 
						className={`execute ${isLoading ? "disabled" : ""}`} 
						onClick={handleRunCommand} 
						disabled={isLoading}
					>
						{isLoading ? "Running..." : "Run Command"}
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
