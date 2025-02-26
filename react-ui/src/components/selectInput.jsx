import React from 'react';

const SelectInput = ({ value, setValue, placeholder = "", options = [] }) => {
  return (
    <div className='selectInput'>
      <label>{placeholder}</label>
      <select value={value} onChange={(e) => setValue(e.target.value)}>
        {options.map((option, index) => (
          <option key={index} value={option.value}>{option.text}</option>
        ))}
      </select>
    </div>
  );
};

export default SelectInput;
