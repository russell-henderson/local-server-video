// Compatibility stub for VR support (archived)
// See docs/deferred/VR_MIGRATION_NOTE.md for details

(function(){
  // No-op VR helpers to avoid 404s when templates reference older VR scripts.
  window.vrSupport = window.vrSupport || {
    enterVRMode: function(){ console.info('vrSupport.enterVRMode() stub called — VR features archived.'); },
    exitVRMode: function(){ console.info('vrSupport.exitVRMode() stub called — VR features archived.'); },
    isVRAvailable: function(){ return false; }
  };
})();
