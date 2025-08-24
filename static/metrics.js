/**
 * Performance Metrics Collection for Local Video Server
 * Captures FPS, memory (when available), theme/preview events
 * Stores in localStorage so you can inspect or ship later to an endpoint
 */

(() => {
  const state = {
    fps: 0,
    last: performance.now(),
    frames: 0,
    mem: null,
    ux: { themeSwitches: 0, darkToggles: 0, previewsStarted: 0, previewsStopped: 0 },
    sampleEveryMs: 1000
  };

  function loop(now) {
    state.frames++;
    const delta = now - state.last;
    if (delta >= state.sampleEveryMs) {
      state.fps = Math.round((state.frames * 1000) / delta);
      state.frames = 0;
      state.last = now;
      capture();
    }
    requestAnimationFrame(loop);
  }

  function capture() {
    if (performance && performance.memory) {
      const { usedJSHeapSize, totalJSHeapSize } = performance.memory;
      state.mem = { used: usedJSHeapSize, total: totalJSHeapSize };
    }
    persist();
  }

  function persist() {
    const payload = {
      t: Date.now(),
      fps: state.fps,
      mem: state.mem,
      ux: state.ux
    };
    localStorage.setItem("lvs:metrics", JSON.stringify(payload));
  }

  // Hook UX events (emitted by our shortcuts & preview code)
  window.addEventListener("ux:themeShortcut", (e) => {
    if (e.detail?.action === "switchTheme") state.ux.themeSwitches++;
    if (e.detail?.action === "toggleDark") state.ux.darkToggles++;
    persist();
  });

  document.addEventListener("preview:start", () => { state.ux.previewsStarted++; persist(); }, true);
  document.addEventListener("preview:stop",  () => { state.ux.previewsStopped++;  persist(); }, true);

  // Expose quick inspector
  window.__LVS_METRICS = () => JSON.parse(localStorage.getItem("lvs:metrics") || "{}");

  // Start monitoring
  requestAnimationFrame(loop);
  
  console.log('📊 Performance metrics collection started');
  console.log('Run __LVS_METRICS() in console to view current metrics');
})();
  