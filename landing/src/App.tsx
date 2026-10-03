import React from 'react';
import { motion } from 'framer-motion';
import { Nav } from './components/Nav';
import { Hero } from './components/Hero';
import { Features } from './components/Features';
import { Benchmarks } from './components/Benchmarks';
import { HowItWorks } from './components/HowItWorks';
import { CTA } from './components/CTA';
import { Footer } from './components/Footer';
import { Rails } from './components/Rails';

// Subtle scroll reveal variant
const sectionReveal = {
  hidden: { opacity: 0, y: 12 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.5,
      ease: [0.22, 1, 0.36, 1],
    },
  },
};

export const App: React.FC = () => {
  return (
      <div className="relative flex min-h-screen flex-col bg-canvas text-ink overflow-x-clip">
      {/* Authentic Framer Rails canvas background in gutters outside 1200px */}
      <Rails
        contentWidth={1200}
        gutter={24}
        density={0.58}
        speed={0.008}
        scrollFactor={0.35}
        stretch={0.55}
        ink="#000000"
        marker="#FFE53B"
      />

      {/* 1. Sticky Nav */}
      <Nav />

      <main className="relative z-10 flex-1">
        {/* 2. Hero Section */}
        <motion.div
          initial="hidden"
          animate="visible"
          variants={sectionReveal}
        >
          <Hero />
        </motion.div>

        {/* 3. How It Works (Workflow) */}
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-60px' }}
          variants={sectionReveal}
        >
          <HowItWorks />
        </motion.div>

        {/* 5. Features Grid */}
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-60px' }}
          variants={sectionReveal}
        >
          <Features />
        </motion.div>

        {/* 6. Benchmarks */}
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-60px' }}
          variants={sectionReveal}
        >
          <Benchmarks />
        </motion.div>

        {/* 7. Final CTA Band */}
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-60px' }}
          variants={sectionReveal}
        >
          <CTA />
        </motion.div>
      </main>

      {/* 8. Footer */}
      <Footer />
    </div>
  );
};

export default App;
