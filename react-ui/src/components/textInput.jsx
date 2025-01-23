import React, { useState } from 'react';

const TextInput = ({ defaultValue }) => {
  const [value, setValue] = useState(defaultValue || "");

  return (
    <input  className={"textInput"} value={value} onChange={(e) => setValue(e.target.value)} />
  );
};

export default TextInput;