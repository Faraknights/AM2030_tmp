import React, { useEffect, useRef, useState } from "react";
import Accordion from "../accordion";

const EmotionRecognition = ({ audioFiles, selectedAudio }) => {
  const [responseMessage, setResponseMessage] = useState([]);
  const [status, setStatus] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const resultRef = useRef(null);

  const labels = {
    title: "Emotion and Intention Recognition",
    full:
      "This module will recognize both the emotion and the intention in the audio sent through the module [Audio Selection]. It will first segment if needed, then transcribe the text before analyzing the voice and the text to determine the user's emotional state and explicit intentions.",
    button: "Analyze audio",
  };

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

  const processResponse = (rawResult) => {
    const lines = rawResult.trim().split("\n");
    const lastLine = lines.pop();

    let emotions = [];

    try {
      emotions = JSON.parse(lastLine);
    } catch {
      emotions = lastLine
        .replace(/[\[\]"']/g, "")
        .split(",")
        .map((e) => e.trim())
        .filter(Boolean);
    }

    const chainOfThought = lines.join("\n").trim();

    return { chainOfThought, emotions };
  };

  const callEmotionAPI = async (text) => {
    const response = await fetch("http://localhost:5000/asr/emotion", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ transcription: text }),
    });
    const data = await response.json();
    return { status: response.status, result: data.result || data.error || "No result received" };
  };

  const callIntentionAPI = async (text) => {
    const response = await fetch("http://localhost:5000/asr/intention_category", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ transcription: text }),
    });
    const data = await response.json();
    return { status: response.status, result: data.result || data.error || "No result received" };
  };

  const callFineIntentionAPI = async (code, text) => {
    const response = await fetch("http://localhost:5000/asr/intention", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ category_code: code, transcription: text }),
    });
    const data = await response.json();
    return {
      status: response.status,
      result: data.result || data.error || "No result received",
    };
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

      const processSentence = async (sentence) => {
        const { status: emotionStatus, result: emotionRaw } = await callEmotionAPI(sentence);
        const { chainOfThought, emotions } = processResponse(emotionRaw);

        const { status: intentionStatus, result: intentionRaw } = await callIntentionAPI(sentence);
        const intentionLines = intentionRaw.trim().split("\n");
        const code = intentionLines[intentionLines.length - 1].replace("*", "").replace("[", "").replace("]", "").trim();

        const { status: fineStatus, result: fineIntention } = await callFineIntentionAPI(code, sentence);
        const intention = fineIntention;

        setResponseMessage((prev) => [
          ...prev,
          { text: sentence, chainOfThought, emotions, intention, status: emotionStatus },
        ]);
        setStatus(emotionStatus);
      };

      if (segment === "T") {
        const sentences = transcription
          .split(/[.,!?]/)
          .map((s) => s.trim())
          .filter(Boolean);

        for (const sentence of sentences) {
          await processSentence(sentence);
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
                {responseMessage.map(({ text, chainOfThought, emotions, intention }, index) => (
                  <div key={index} style={{ marginBottom: "1rem" }}>
                    <strong>Input:</strong> <span>{text}</span>

                    {chainOfThought && (
                      <div style={{ whiteSpace: "pre-wrap", marginTop: "0.25rem", fontStyle: "italic" }}>
                        {chainOfThought}
                      </div>
                    )}

                    {emotions && emotions.length > 0 && (
                      <div style={{ marginTop: "0.5rem" }}>
                        <strong>Detected Emotions:</strong> {emotions.join(", ")}
                      </div>
                    )}

                    {intention && (
                      <div style={{ marginTop: "0.5rem" }}>
                        <strong>Detected Intention:</strong> {intention}
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
