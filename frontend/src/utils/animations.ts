import type { Variants } from 'framer-motion'

// Screen Fade/Scale Transition
export const screenVariants: Variants = {
  initial: {
    opacity: 0,
    y: 16,
    scale: 0.98,
  },
  animate: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      duration: 0.45,
      ease: [0.16, 1, 0.3, 1],
      staggerChildren: 0.08,
    },
  },
  exit: {
    opacity: 0,
    y: -16,
    scale: 0.98,
    transition: {
      duration: 0.3,
      ease: [0.7, 0, 0.84, 0],
    },
  },
}

// Stagger Container
export const staggerContainer: Variants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.08,
      delayChildren: 0.1,
    },
  },
}

// Stagger Item (for table rows, list items)
export const staggerItem: Variants = {
  hidden: { opacity: 0, x: -16, y: 6 },
  show: {
    opacity: 1,
    x: 0,
    y: 0,
    transition: {
      type: 'spring',
      stiffness: 350,
      damping: 24,
    },
  },
}

// Reticle Box Pop-in
export const reticleVariants: Variants = {
  hidden: {
    opacity: 0,
    scale: 1.25,
    filter: 'blur(4px)',
  },
  visible: (i: number = 0) => ({
    opacity: 1,
    scale: 1,
    filter: 'blur(0px)',
    transition: {
      delay: i * 0.28,
      duration: 0.4,
      ease: [0.34, 1.56, 0.64, 1], // snappy overshoot spring
    },
  }),
  exit: {
    opacity: 0,
    scale: 0.9,
    transition: { duration: 0.2 },
  },
}

// 3D Verdict Reveal Card Flip
export const verdictFlipVariants: Variants = {
  hidden: {
    opacity: 0,
    rotateX: -75,
    scale: 0.88,
    transformPerspective: 1200,
  },
  visible: {
    opacity: 1,
    rotateX: 0,
    scale: 1,
    transition: {
      type: 'spring',
      stiffness: 220,
      damping: 20,
      delay: 0.15,
    },
  },
}

// Fake Verdict Alert Shake
export const alertShakeVariants: Variants = {
  shake: {
    x: [0, -10, 10, -8, 8, -4, 4, 0],
    transition: {
      duration: 0.55,
      ease: 'easeInOut',
      delay: 0.35,
    },
  },
}

// Accordion Expand/Collapse
export const accordionVariants: Variants = {
  collapsed: {
    height: 0,
    opacity: 0,
    overflow: 'hidden',
    transition: {
      height: { duration: 0.3, ease: [0.4, 0, 0.2, 1] },
      opacity: { duration: 0.2 },
    },
  },
  expanded: {
    height: 'auto',
    opacity: 1,
    overflow: 'visible',
    transition: {
      height: { duration: 0.35, ease: [0.04, 0.62, 0.23, 0.98] },
      opacity: { duration: 0.3, delay: 0.08 },
    },
  },
}

// Drop Preview Card Slide In
export const previewCardVariants: Variants = {
  hidden: {
    opacity: 0,
    scale: 0.85,
    y: 30,
  },
  visible: {
    opacity: 1,
    scale: 1,
    y: 0,
    transition: {
      type: 'spring',
      stiffness: 280,
      damping: 22,
    },
  },
  exit: {
    opacity: 0,
    scale: 0.85,
    y: -20,
    transition: { duration: 0.25 },
  },
}
