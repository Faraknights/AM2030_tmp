import React from 'react';

const TextInput = ({ value, setValue, placeholder = "", hasError = false }) => {
  return (
    <div className="textInputContainer">
      <input 
        className={`textInput ${hasError ? 'error' : ''}`} 
        value={value} 
        onChange={(e) => setValue(e.target.value)} 
      />
      <label className={`textInputLabel ${value ? 'active' : ''}`}>{placeholder}</label>
    </div>
  );
};

export default TextInput;
