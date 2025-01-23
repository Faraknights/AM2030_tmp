import React, { useState } from 'react';

const Accordion = (params) => {
  const {title, content} = params
  const [isOpen, setIsOpen] = useState(true);

  const handleToggle = () => {
    setIsOpen(!isOpen);
  };

  return (
    <div className="accordion">
      <div className="accordion-item">
        <button
          className={`accordion-header ${isOpen ? 'active' : ''}`}
          onClick={handleToggle}
        >
          <div className='arrow'></div>
          {title}
        </button>
        <div className={`accordion-content ${isOpen ? 'show' : ''}`}>
          <div>
            {content}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Accordion;
