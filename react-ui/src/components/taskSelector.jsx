import React, { useEffect } from "react";

const TaskSelector = ({ selectedTask, setSelectedTask, loadingTask, setLoadingTask }) => {
  const tasks = [
    { label: "Emotion", value: "emotion" },
    { label: "Intention", value: "intention" },
  ];

  useEffect(() => {
    handleClick("emotion")
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleClick = async (taskValue) => {
    setSelectedTask(taskValue);
    setLoadingTask(taskValue);

    const requestData = { task: taskValue };

    try {
      const response = await fetch("http://localhost:5000/asr/cacheModel", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`);
      }

      const data = await response.json();
      console.log("Response:", data);
    } catch (error) {
      console.error("Error:", error);
    } finally {
      setLoadingTask(null);
    }
  };

  return (
    <div className="taskSelector">
      {tasks.map((task) => (
        <button
          key={task.value}
          onClick={() => handleClick(task.value)}
          className={"task" + (task.value === selectedTask ? " selected" : "")}
          disabled={loadingTask !== null}
        >
          {loadingTask === task.value ? "Preparing..." : task.label}
        </button>
      ))}
    </div>
  );
};

export default TaskSelector;
