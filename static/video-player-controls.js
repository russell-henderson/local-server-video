// video-player-controls.js
// Auto-hide player controls: show on mousemove/hover, hide after idle, handle fullscreen
(function () {
  const IDLE_MS = 2000;

  function makeController(container) {
    const controls = container.querySelector('[data-controls]');
    if (!controls) return null;

    let idleTimer = null;

    function show() {
      container.classList.add('controls-visible');
      if (idleTimer) clearTimeout(idleTimer);
      idleTimer = setTimeout(() => { container.classList.remove('controls-visible'); }, IDLE_MS);
    }

    function hide() {
      container.classList.remove('controls-visible');
      if (idleTimer) { clearTimeout(idleTimer); idleTimer = null; }
    }

    function onMouseMove() { show(); }
    function onMouseEnter() { show(); }
    function onMouseLeave() { hide(); }
    function onTouchStart() { show(); }
    function onFullscreenChange() {
      // When entering fullscreen, briefly show controls so users know they exist
      show();
    }

    container.addEventListener('mousemove', onMouseMove);
    container.addEventListener('mouseenter', onMouseEnter);
    container.addEventListener('mouseleave', onMouseLeave);
    container.addEventListener('touchstart', onTouchStart, { passive: true });

    document.addEventListener('fullscreenchange', onFullscreenChange);
    document.addEventListener('webkitfullscreenchange', onFullscreenChange);

    // Initial state: hide; show briefly on load for discoverability
    show();
    return { show, hide };
  }

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-player]').forEach(player => {
      try { makeController(player); } catch (ex) { console.error('player-controls init error', ex); }
    });
  });
})();
