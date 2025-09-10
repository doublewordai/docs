---
sidebar_position: 1
sidebar_label: Home
slug: /
hide_table_of_contents: true
hide_title: true
---

import controlLayerIcon from './assets/control-layer.webp';
import inferenceStackIcon from './assets/inference-stack.webp';

<div className="visitor-paths visitor-paths-horizontal">
  
  <a href="./control-layer/" className="path-card-link path-card-link-flex">
    <div className="path-card control-path path-card-flex">
      <div className="path-icon">
        <img src={controlLayerIcon} alt="Control Layer" className="path-icon-image" />
      </div>
      <div className="path-header">
        <h2>Already Using AI APIs?</h2>
        <p className="path-tagline">Centralize • Secure • Control</p>
      </div>
      <div className="path-content">
        <p>Perfect for <strong>admins</strong> and <strong>teams</strong> who want enterprise control over AI access.</p>
      </div>
    </div>
  </a>


  <a href="./inference-stack/" className="path-card-link path-card-link-flex">
    <div className="path-card inference-path path-card-flex">
      <div className="path-icon">
        <img src={inferenceStackIcon} alt="Inference Stack" className="path-icon-image" />
      </div>
      <div className="path-header">
        <h2>Want to Self-Host AI Models?</h2>
        <p className="path-tagline">Deploy • Scale • Own</p>
      </div>
      <div className="path-content">
        <p>Perfect for <strong>engineers</strong> and <strong>organizations</strong> who want to run models in their own environment.</p>
      </div>
    </div>
  </a>

</div>
<div className="homepage-footer">
  <div className="footer-content">
    <h3>Need Help Getting Started?</h3>
    <p>Get expert guidance on implementing the right AI platform solution for your organization.</p>
    <p>Contact: <a href="mailto:hello@doubleword.ai">hello@doubleword.ai</a></p>
  </div>
</div>
