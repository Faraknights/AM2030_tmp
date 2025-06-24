import React, { useEffect, useRef, useState } from "react";
import Accordion from "../accordion";

const labels = {
  title: "Emotion and Intention Recognition",
  full:
    "This module will recognize both the emotion and the intention in the audio sent through the module [Audio Selection]. It will first segment if needed, then transcribe the text before analyzing the voice and the text to determine the user's emotional state and explicit intentions.",
  button: "Analyze audio",
};

// Unified API call function
const callASRApi = async (endpoint, bodyObj) => {
  const response = await fetch(`http://localhost:5000/asr/${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(bodyObj),
  });
  const data = await response.json();
  return {
    status: response.status,
    result: data.result || data.error || "No result received",
  };
};

// Unified response processor
export const processResponse = (rawResult) => {
  const lines = rawResult.trim().split("\n");
  const lastLine = lines.pop();

  let code = [];

  try {
    code = JSON.parse(lastLine);
  } catch {
    code = lastLine
      .replace(/[\[\]"']/g, "")
      .split(",")
      .map((e) => e.trim())
      .filter(Boolean);
  }

  const chainOfThought = lines.join("\n").trim();

  return { chainOfThought, code };
};

const EmotionRecognition = ({ audioFiles, selectedAudio }) => {
  const [responseMessage, setResponseMessage] = useState([]);
  const [status, setStatus] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const resultRef = useRef(null);

  useEffect(() => {
    if (resultRef.current) {
      resultRef.current.scrollTop = resultRef.current.scrollHeight;
    }
  }, [responseMessage]);

  const isAudioValid =
    audioFiles &&
    selectedAudio !== null &&
    audioFiles[selectedAudio] &&
    audioFiles[selectedAudio].transcription &&
    audioFiles[selectedAudio].transcription.trim() !== "";

  const processSentence = async (sentence) => {
    // Start with an empty entry for this sentence
    setResponseMessage((prev) => [
      ...prev,
      {
        text: sentence,
        emotionCoT: "",
        intentionCoT: "",
        fineIntentionCoT: "",
        categoryCode: "",
        emotions: [],
        intention: "",
        status: null,
      },
    ]);

    // 1. Emotion API call
    const { status: emotionStatus, result: emotionRaw } = await callASRApi("emotion", { transcription: sentence });
    const { chainOfThought: emotionCoT, code: emotions } = processResponse(emotionRaw);

    setResponseMessage((prev) =>
      prev.map((item) =>
        item.text === sentence
          ? { ...item, emotionCoT, emotions, status: emotionStatus }
          : item
      )
    );

    // 2. Intention Category API call
    const { status: intentionStatus, result: intentionRaw } = await callASRApi("intention_category", { transcription: sentence });
    const { chainOfThought: intentionCoT, code: intentionCodes } = processResponse(intentionRaw);
    const categoryCode = intentionCodes.length > 0 ? intentionCodes[0] : "";

    setResponseMessage((prev) =>
      prev.map((item) =>
        item.text === sentence
          ? { ...item, intentionCoT, categoryCode }
          : item
      )
    );

    // 3. Fine Intention API call
    const { status: fineStatus, result: fineIntentionRaw } = await callASRApi("intention", {
      category_code: categoryCode,
      transcription: sentence,
    });
    const { chainOfThought: fineIntentionCoT, code: fineIntentionCodes } = processResponse(fineIntentionRaw);
    const intention = fineIntentionCodes.length > 0 ? fineIntentionCodes[0] : "";

    setResponseMessage((prev) =>
      prev.map((item) =>
        item.text === sentence
          ? { ...item, fineIntentionCoT, intention }
          : item
      )
    );

    // Update status with last call's status (optional)
    setStatus(fineStatus);
  };


  const handleRunCommand = async () => {
    setResponseMessage([]);
    setStatus(null);

    if (!isAudioValid) {
      setResponseMessage([{ text: "No audio transcription available.", output: "" }]);
      setStatus(400);
      return;
    }

    setIsLoading(true);

    try {
      const { transcription, segment } = audioFiles[selectedAudio];

      if (segment === "T") {
        const sentences = transcription
          .split(/[.,!?]/)
          .map((s) => s.trim())
          .filter(Boolean);

        for (const sentence of sentences) {
          await processSentence(sentence);
          // Small delay for UX smoothness
          await new Promise((resolve) => setTimeout(resolve, 100));
        }
      } else {
        await processSentence(transcription);
      }
    } catch (error) {
      setResponseMessage([
        { text: "Error", chainOfThought: "", emotions: [], intention: "", output: error.message },
      ]);
      setStatus(500);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Accordion
      title={labels.title}
      content={
        <div id="runCommand">
          <span className="description">{labels.full}</span>

          {!audioFiles || selectedAudio === null ? (
            <span className="warning">⚠ Warning: You must select an audio file.</span>
          ) : !isAudioValid ? (
            <span className="warning">
              ⚠ Warning: The selected audio must have a full transcription to be sent to the model.
            </span>
          ) : null}

          <button
            className={`execute ${isLoading || !isAudioValid ? "disabled" : ""}`}
            onClick={handleRunCommand}
            disabled={isLoading || !isAudioValid}
          >
            {isLoading ? "Running..." : labels.button}
          </button>

          {responseMessage.length > 0 && (
            <>
              <span className="resultTitle">Status: {status}</span>
              <div ref={resultRef} className={`result ${status === 200 ? "success" : "fail"}`}>
                {responseMessage.map(({ text, emotionCoT, intentionCoT, fineIntentionCoT, categoryCode, emotions, intention }, index) => (
                  <div key={index} className="result-item" style={{ marginBottom: "1rem" }}>
                    <strong>Input:</strong> <span className="input-text">{text}</span>

                    {emotionCoT && (
                      <div className="chain-of-thought emotion-cot">
                        {emotionCoT}
                      </div>
                    )}

                    {emotions && emotions.length > 0 && (
                      <div className="code">
                        {emotions.join(", ")}
                      </div>
                    )}

                    {intentionCoT && (
                      <div className="chain-of-thought intention-category-cot">
                        {intentionCoT}
                      </div>
                    )}

                    {categoryCode && (
                      <div className="code">
                        {Array.isArray(categoryCode) ? categoryCode.join(", ") : categoryCode}
                      </div>
                    )}

                    {fineIntentionCoT && (
                      <div className="chain-of-thought fine-intention-cot">
                        {fineIntentionCoT}
                      </div>
                    )}

                    {intention && (
                      <div className="code">
                        {intention}
                      </div>
                    )}
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
