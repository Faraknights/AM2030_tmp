import React, { useState } from "react";
import Accordion from "../accordion";

const RunCommand = () => {
	const [params, setParams] = useState([{ name: "param1", value: "Hello" }, { name: "param2", value: "world" }]);
	const [responseMessage, setResponseMessage] = useState("");
	const [status, setStatus] = useState(null);

	const handleRunCommand = async () => {
		const paramData = params.reduce((acc, param) => {
			acc[param.name] = param.value;
			return acc;
		}, {});

		try {
			const response = await fetch("http://localhost:5000/run/", {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: JSON.stringify(paramData),
			});
			const data = await response.json();
			console.log(data)
			setResponseMessage(data.stdout || data.error);
			setStatus(response.status);
		} catch (error) {
			console.error("Error running command:", error);
			setResponseMessage(error.message);
			setStatus(500);
		}
	};

	const handleParamChange = (index, key, value) => {
		const newParams = [...params];
		newParams[index][key] = value;
		setParams(newParams);
	};

	const addParam = () => {
		setParams([...params, { name: "", value: "" }]);
	};

	const removeParam = (index) => {
		const newParams = params.filter((_, i) => i !== index);
		setParams(newParams);
	};

	return (
		<Accordion
			title={"Run Command"}
			content={
				<div id="runCommand">
					<span className="description">
						Provide parameter values to execute the command.
					</span>
					<div className="paramInputs">
						{params.map((param, index) => (
							<div key={index} className="paramPair">
								<input
                                    className="parameterName textInput"
									type="text"
									placeholder="Parameter Name"
									value={param.name}
									onChange={(e) => handleParamChange(index, "name", e.target.value)}
								/>
								<input
                                    className="parameterValue textInput"
									type="text"
									placeholder="Parameter Value"
									value={param.value}
									onChange={(e) => handleParamChange(index, "value", e.target.value)}
								/>
								<button className="removeParam" onClick={() => removeParam(index)}><span></span></button>
							</div>
						))}
						<button className="addParam" onClick={addParam}>Add Parameter</button>
					</div>
					<button className="execute" onClick={handleRunCommand}>Run Command</button>
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

export default RunCommand;
