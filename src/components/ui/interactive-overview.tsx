import React from 'react';

const InteractiveOverview: React.FC = () => {
  const handleControlLayerClick = () => {
    window.location.href = './control-layer/';
  };

  const handleInferenceStackClick = () => {
    window.location.href = './inference-stack/';
  };

  return (
    <div style={{ position: 'relative', display: 'inline-block', maxWidth: '100%' }}>
      {/* SVG Background */}
      <img
        src="/docs/img/overview.svg"
        alt="Titan AI Platform Overview"
        style={{
          width: '100%',
          height: 'auto',
          maxHeight: '60vh',
          objectFit: 'contain',
          display: 'block'
        }}
      />
      
      {/* Control Layer Clickable Area - Left side */}
      <button
        onClick={handleControlLayerClick}
        style={{
          position: 'absolute',
          top: '29%',
          left: '22%',
          width: '56%',
          height: '13%',
          backgroundColor: 'transparent',
          border: '2px solid transparent',
          borderRadius: '8px',
          cursor: 'pointer',
          zIndex: 10,
          transition: 'all 0.2s ease'
        }}
        title="Go to Control Layer"
        aria-label="Navigate to Control Layer documentation"
      />
      
      {/* Inference Stack Clickable Area - Right side */}
      <button
        onClick={handleInferenceStackClick}
        style={{
          position: 'absolute',
          top: '50%',
          right: '22%',
          width: '28%',
          height: '13%',
          backgroundColor: 'transparent',
          border: '2px solid transparent',
          borderRadius: '8px',
          cursor: 'pointer',
          zIndex: 10,
          transition: 'all 0.2s ease'
        }}
        title="Go to Inference Stack"
        aria-label="Navigate to Inference Stack documentation"
      />
    </div>
  );
};

export default InteractiveOverview;