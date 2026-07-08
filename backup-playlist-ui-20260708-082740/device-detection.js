// Compatibility stub for device detection (archived)
// See docs/deferred/VR_MIGRATION_NOTE.md for details

(function(){
  // This file intentionally no-ops. If you need device detection for VR features,
  // restore the archived implementation from docs/deferred/.
  window.deviceDetection = window.deviceDetection || {
    isVR: false,
    isMobile: false,
    detect: function(){ return { isVR: false, isMobile: false }; }
  };
})();
