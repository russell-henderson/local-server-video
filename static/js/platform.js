/**
 * static/js/platform.js
 * Platform detection utility for adaptive behavior across desktop, mobile, and VR
 * Exports platform properties to make input/interaction decisions
 */

export const platform = {
  // Touch pointer detection (coarse pointer = touch, fine pointer = mouse/stylus)
  isTouch: matchMedia('(pointer: coarse)').matches,

  // Hover capability (hover: hover = has hover, hover: none = no hover)
  hasHover: matchMedia('(hover: hover)').matches,

  // VR device detection (check user agent for Quest, Oculus, or similar)
  isQuest: /OculusBrowser|Quest|Oculus/i.test(navigator.userAgent),

  // Get combined input modality hint
  getInputMode: () => {
    if (platform.isQuest) return 'vr';
    if (platform.isTouch && !platform.hasHover) return 'touch';
    if (platform.hasHover) return 'pointer';
    return 'keyboard';
  },

  // Detect if we're in a mobile viewport
  isMobile: () => window.innerWidth < 768,
};

// Log platform detection for debugging
if (window.location.search.includes('debug=platform')) {
  console.log('Platform Detection:', {
    isTouch: platform.isTouch,
    hasHover: platform.hasHover,
    isQuest: platform.isQuest,
    inputMode: platform.getInputMode(),
    isMobile: platform.isMobile(),
    userAgent: navigator.userAgent,
  });
}
