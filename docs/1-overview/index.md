---
sidebar_position: 1
sidebar_label: Overview
slug: /
hide_table_of_contents: true
---

import gcp1 from './assets/gcp1.png';
import gcp2 from './assets/gcp2.png';
import gcp3 from './assets/gcp3.png';
import sage from './assets/Arch_Amazon-SageMaker_64.png';
import eks from './assets/Arch_Amazon-EKS-Cloud_64.png';
import ec2 from './assets/Arch_Amazon-EC2_64.png';
import snow from './assets/snowflake.png';
import azure from './assets/aks.png';

import Slider from "react-infinite-logo-slider";
import MySlider from './slider';

<div className="homepage-hero">
  <div className="hero-content">
    <h1 className="hero-title">Production-Ready AI Platform</h1>
    <p className="hero-subtitle">Deploy and manage Large Language Models with enterprise-grade security, scalability, and control</p>
  </div>
</div>

<div className="visitor-paths visitor-paths-horizontal">
  
  <a href="./control-layer/" className="path-card-link path-card-link-flex">
    <div className="path-card control-path path-card-flex">
      <div className="path-icon">
        🛡️
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

  <div className="path-divider path-divider-vertical">
    <span>OR</span>
  </div>

  <a href="./inference-stack/" className="path-card-link path-card-link-flex">
    <div className="path-card inference-path path-card-flex">
      <div className="path-icon">
        ⚡
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

<div className="deployment-showcase">
  <MySlider
    width="120px"
    duration={12}
    pauseOnHover={true}
    blurBorders={true}
    blurBorderColor={'#ffffff'}
    id={"slide"}
  >
    <Slider.Slide>
      <div className="flex flex-col items-center">
        <img src={gcp1} alt="Vertex AI" width={80} className="w-24"/>
        <p className={"caro"}>Vertex</p>
      </div>
    </Slider.Slide>
    <Slider.Slide>
      <div className="flex flex-col items-center">
        <img src={gcp2} alt="Google Kubernetes Engine" width={80} className="w-24"/>
        <p className={"caro"}>GKE</p>
      </div>
    </Slider.Slide>
    <Slider.Slide>
      <div className="flex flex-col items-center">
        <img src={gcp3} alt="Google Compute Engine" width={80} className="w-24"/>
        <p className={"caro"}>GCE</p>
      </div>
    </Slider.Slide>
    <Slider.Slide>
      <div className="flex flex-col items-center">
        <img src={azure} alt="Azure Kubernetes Service" height={80} className="w-24"/>
        <p className={"caro"}>AKS</p>
      </div>
    </Slider.Slide>
    <Slider.Slide>
      <div className="flex flex-col items-center">
        <img src={snow} alt="Snowflake" width={80} className="w-24"/>
        <p className={"caro"}>Snowpark</p>
      </div>
    </Slider.Slide>
    <Slider.Slide>
      <div className="flex flex-col items-center">
        <img src={ec2} alt="Amazon EC2" width={80} className="w-24"/>
        <p className={"caro"}>EC2</p>
      </div>
    </Slider.Slide>
    <Slider.Slide>
      <div className="flex flex-col items-center">
        <img src={eks} alt="Amazon EKS" width={80} className="w-24"/>
        <p className={"caro"}>EKS</p>
      </div>
    </Slider.Slide>
    <Slider.Slide>
      <div className="flex flex-col items-center">
        <img src={sage} alt="Amazon SageMaker" width={80} className="w-24"/>
        <p className={"caro"}>SageMaker</p>
      </div>
    </Slider.Slide>
  </MySlider>
</div>


<div className="homepage-footer">
  <div className="footer-content">
    <h3>Need Help Getting Started?</h3>
    <p>Get expert guidance on implementing the right AI platform solution for your organization.</p>
    <div className="contact-cta">
      <p>Contact: <a href="mailto:hello@doubleword.ai">hello@doubleword.ai</a></p>
    </div>
  </div>
</div>

