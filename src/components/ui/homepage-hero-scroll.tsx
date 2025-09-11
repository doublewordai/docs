'use client';

import { useScroll, useTransform, motion, MotionValue } from 'framer-motion';
import React, { useRef, forwardRef } from 'react';
import InteractiveOverview from './interactive-overview';

interface SectionProps {
  scrollYProgress: MotionValue<number>;
}

const Section1: React.FC<SectionProps> = ({ scrollYProgress }) => {
  const scale = useTransform(scrollYProgress, [0, 1], [1, 0.8]);
  const rotate = useTransform(scrollYProgress, [0, 1], [0, -5]);
  
  return (
    <motion.section
      style={{ scale, rotate }}
      className='sticky font-semibold top-0 h-screen flex flex-col items-center justify-center text-black'
      // Use the same background as the rest of your site
      style={{
        scale,
        rotate,
        backgroundColor: 'var(--ifm-background-color)'
      }}
    >
      <div className='text-center max-w-6xl mx-auto px-8'>
        <h1 className='text-4xl md:text-6xl font-bold mb-8 leading-tight'>
          Any model. <br />
          <span className='text-4xl md:text-7xl'>Your infrastructure.</span>
        </h1>
        
        <div className='mt-8 max-w-4xl mx-auto'>
          <InteractiveOverview />
        </div>
      </div>
    </motion.section>
  );
};

const Section2: React.FC<SectionProps> = ({ scrollYProgress }) => {
  const scale = useTransform(scrollYProgress, [0, 1], [0.8, 1]);
  const rotate = useTransform(scrollYProgress, [0, 1], [5, 0]);

  return (
    <motion.section
      style={{ 
        scale, 
        rotate,
        backgroundColor: 'var(--ifm-background-color)'
      }}
      className='relative h-screen flex items-center justify-center'
    >
      <div className='homepage-paths-section'>
        <div className='visitor-paths visitor-paths-horizontal'>
          
          <a href="./control-layer/" className="path-card-link path-card-link-flex">
            <div className="path-card control-path path-card-flex">
              <div className="path-icon">
                <img src="/docs/img/control-layer.webp" alt="Control Layer" className="path-icon-image" />
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
                <img src="/docs/img/inference-stack.webp" alt="Inference Stack" className="path-icon-image" />
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
      </div>
    </motion.section>
  );
};

const HomepageHeroScroll = forwardRef<HTMLElement>((props, ref) => {
  const container = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: container,
    offset: ['start start', 'end end'],
  });

  return (
    <main ref={container} className='relative h-[200vh]'>
      <Section1 scrollYProgress={scrollYProgress} />
      <Section2 scrollYProgress={scrollYProgress} />
    </main>
  );
});

HomepageHeroScroll.displayName = 'HomepageHeroScroll';

export default HomepageHeroScroll;