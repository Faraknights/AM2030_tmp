import React, { useState, useEffect, useRef } from 'react';

const Accordion = ({ title, content }) => {
  const [isOpen, setIsOpen] = useState(true);
  const contentRef = useRef(null);

  const handleToggle = () => {
    setIsOpen(!isOpen);
  };

  useEffect(() => {
    if (contentRef.current) {
      contentRef.current.scrollTop = contentRef.current.scrollHeight;
    }
  }, [content]);

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
        <div className={`accordion-content ${isOpen ? 'show' : ''}`} ref={contentRef}>
          <div>
            {content}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Accordion;
