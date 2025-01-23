import React, { useState } from "react";
import Accordion from "../accordion";

const SentimentAnalysis = () => {
	const [value, setValue] = useState("The music is very good");
	const [result, setResult] = useState(null);
	const [status, setStatus] = useState(null);

	const handleExecute = async () => {
		try {
			const response = await fetch("http://localhost:5000/sentiment/", {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: JSON.stringify({ text: value }),
			});
			const resultData = await response.json();
			setResult(resultData);
			setStatus(response.status);
			console.log("Sentiment Analysis Result:", resultData);
		} catch (error) {
			console.error("Error executing sentiment analysis:", error);
			const errorMessage = typeof error.message === "string" 
				? error.message 
				: JSON.stringify(error);

			setResult(errorMessage);
			setStatus(500);
		}
	};

	return (
		<Accordion
			title={"Sentiment Analysis"}
			content={
				<div id="sentiment">
					<span className="description">Returns the sentiment analysis of a given text\nIf the text in input contains the word 'good', then the result is 'happy'. It is a proof of concept, with confidence always at 95%.</span>
					<div className="commandInput">
						<label>Text Input</label>
						<input
							className={"textInput"}
							value={value}
							onChange={(e) => setValue(e.target.value)}
						/>
					</div>
					<button className="execute" onClick={handleExecute}>
						Execute
					</button>
					{result && status === 200 && (
						<>
							<span className="resultTitle">Status: {status}</span>
							<div className={`result success`}>
								<span>Sentiment: {result.sentiment}</span>
								<span>Confidence: {result.confidence}</span>
							</div>
						</>
					)}
					{result && status !== 200 && (
						<>
							<span className="resultTitle">Status: {status}</span>
							<div className={`result fail`}>
								{typeof result === "string" ? result : JSON.stringify(result)}
							</div>
						</>
					)}
				</div>
			}
		/>
	);
};

export default SentimentAnalysis;
