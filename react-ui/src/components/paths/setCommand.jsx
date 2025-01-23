import React, { useState } from "react";
import Accordion from "../accordion";

const SetCommand = () => {
	const [command, setCommand] = useState("echo {param1} {param2}");
	const [responseMessage, setResponseMessage] = useState("");
	const [status, setStatus] = useState(null);

	const handleSetCommand = async () => {
		try {
			const response = await fetch("http://localhost:5000/run/setCommand", {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: JSON.stringify({ command: command }),
			});
			const data = await response.json();
			setResponseMessage(data.message || data.error);
			setStatus(response.status);
		} catch (error) {
			console.error("Error setting command:", error);
			setResponseMessage(error.message);
			setStatus(500);
		}
	};

	return (
		<Accordion
			title={"Set Command"}
			content={
				<div id="setCommand">
					<span className="description">
						Sets the command that will be executed when running the /run endpoint. 
						Use {`{param1..n}`} as placeholders for input parameters.
					</span>
					<div className="commandInput">
						<label>Command Input</label>
						<input
							className={"textInput"}
							value={command}
							onChange={(e) => setCommand(e.target.value)}
						/>
					</div>
					<button className="execute" onClick={handleSetCommand}>
						Set Command
					</button>
					
                    <span className="resultTitle">Status: {status}</span>
					{responseMessage && (
						<div className={`result ${status === 200 ? "success" : "fail"}`}>
							<div>{responseMessage}</div>
						</div>
					)}
				</div>
			}
		/>
	);
};

export default SetCommand;
