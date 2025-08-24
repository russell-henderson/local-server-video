/* ==========================================================================
  Local Video Server — Analytics (no visible test panel)
  --------------------------------------------------------------------------
  What you get:
    • Play/Pause/Seek/Ended/Visibility analytics
    • Periodic “heartbeat” pings with currentTime & watch progress
    • Robust send (sendBeacon → fetch → local queue w/ retry)
    • Console diagnostics (kept)
    • NO UI test panel (suppressed by default)
      - Re-enable only when needed with ?analyticsTest=1
  ========================================================================== */

  (() => {
    const NS = "LVS_ANALYTICS";
    const VERSION = "2.0.0";
    const DEFAULT_ENDPOINT = "/analytics/event"; // change if needed
    const HEARTBEAT_MS = 15000; // 15s
    const SEND_TIMEOUT_MS = 4000;
    const STORAGE_KEY_QUEUE = "__lvs_analytics_queue__";
    const STORAGE_KEY_SESSION = "__lvs_analytics_session__";
  
    // ---- Test panel suppression (always OFF unless URL overrides)
    const url = new URL(window.location.href);
    const TEST_MODE = url.searchParams.has("analyticsTest"); // only shown if ?analyticsTest=1
    const HIDE_EXISTING_TEST_UI = () => {
      // In case an older script injected a panel, remove it.
      const ids = ["analytics-test-panel", "lvs-analytics-test-panel"];
      ids.forEach((id) => {
        const el = document.getElementById(id);
        if (el && el.parentNode) el.parentNode.removeChild(el);
      });
    };
  
    // ---- Small utilities
    const nowIso = () => new Date().toISOString();
    const clamp = (n, min, max) => Math.max(min, Math.min(max, n));
    const throttle = (fn, ms) => {
      let last = 0, pending;
      return (...args) => {
        const t = Date.now();
        if (t - last >= ms) {
          last = t; fn(...args);
        } else {
          clearTimeout(pending);
          pending = setTimeout(() => { last = Date.now(); fn(...args); }, ms - (t - last));
        }
      };
    };
  
    // ---- Local queue (for offline / retry)
    const loadQueue = () => {
      try { return JSON.parse(localStorage.getItem(STORAGE_KEY_QUEUE) || "[]"); }
      catch { return []; }
    };
    const saveQueue = (q) => {
      try { localStorage.setItem(STORAGE_KEY_QUEUE, JSON.stringify(q)); } catch {}
    };
    const pushQueue = (evt) => { const q = loadQueue(); q.push(evt); saveQueue(q); };
  
    // ---- Session id (stable while tab open; persisted to survive reloads)
    const getSessionId = () => {
      try {
        let s = sessionStorage.getItem(STORAGE_KEY_SESSION);
        if (!s) {
          s = crypto.randomUUID ? crypto.randomUUID() : (Math.random().toString(36).slice(2) + Date.now());
          sessionStorage.setItem(STORAGE_KEY_SESSION, s);
        }
        return s;
      } catch {
        return Math.random().toString(36).slice(2) + Date.now();
      }
    };
  
    // ---- Sender
    async function sendEvent(evt, endpoint) {
      // Prefer sendBeacon (non-blocking on unload)
      const payload = JSON.stringify(evt);
      const headers = { type: "application/json" };
  
      if (navigator.sendBeacon) {
        const ok = navigator.sendBeacon(endpoint, new Blob([payload], headers));
        if (ok) return true;
      }
  
      // Fallback to fetch (with timeout)
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), SEND_TIMEOUT_MS);
      try {
        const res = await fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: payload,
          keepalive: true,
          signal: controller.signal,
        });
        clearTimeout(timer);
        return res.ok;
      } catch {
        clearTimeout(timer);
        return false;
      }
    }
  
    async function flushQueue(endpoint) {
      const q = loadQueue();
      if (!q.length) return;
      const remain = [];
      for (const evt of q) {
        /* eslint-disable no-await-in-loop */
        const ok = await sendEvent(evt, endpoint);
        if (!ok) remain.push(evt);
        /* eslint-enable no-await-in-loop */
      }
      saveQueue(remain);
    }
  
    // ---- Core tracker
    class Analytics {
      constructor(video, options = {}) {
        this.video = video;
        this.opts = {
          endpoint: options.endpoint || DEFAULT_ENDPOINT,
          videoId: options.videoId || video?.dataset?.filename || document.title || "unknown",
          userId: options.userId || null,
          extra: options.extra || {},
          console: options.console !== false, // keep console logs by default
        };
        this.sessionId = getSessionId();
        this.startedAt = nowIso();
        this.heartbeatTimer = null;
        this.lastHeartbeatProgress = -1;
        this.bound = false;
  
        if (!video) {
          this.log("No <video> element provided; analytics disabled.");
          return;
        }
        this.bind();
        // Start a heartbeat loop
        this.heartbeatTimer = setInterval(() => this.heartbeat(), HEARTBEAT_MS);
        // Try to flush any pending events on load
        flushQueue(this.opts.endpoint);
        this.log(`Initialized (v${VERSION}) for`, this.opts.videoId);
      }
  
      log(...args) {
        if (this.opts.console) {
          // eslint-disable-next-line no-console
          console.log("[LVS:analytics]", ...args);
        }
      }
  
      // Compute % watched
      progressPct() {
        const dur = Number(this.video.duration) || 0;
        const cur = Number(this.video.currentTime) || 0;
        if (!dur) return 0;
        return clamp(Math.round((cur / dur) * 100), 0, 100);
      }
  
      baseEvent(type, overrides = {}) {
        return {
          _v: VERSION,
          type,
          ts: nowIso(),
          sessionId: this.sessionId,
          videoId: this.opts.videoId,
          userId: this.opts.userId,
          href: location.href,
          visibility: document.visibilityState,
          currentTime: Number(this.video.currentTime) || 0,
          duration: Number(this.video.duration) || 0,
          progressPct: this.progressPct(),
          extra: this.opts.extra,
          ...overrides,
        };
      }
  
      async emit(evt) {
        const ok = await sendEvent(evt, this.opts.endpoint);
        if (!ok) pushQueue(evt);
      }
  
      bind() {
        if (this.bound) return;
        this.bound = true;
  
        this.video.addEventListener("play", () => this.emit(this.baseEvent("play")));
        this.video.addEventListener("pause", () => this.emit(this.baseEvent("pause")));
        this.video.addEventListener("ended", () => this.emit(this.baseEvent("ended")));
        this.video.addEventListener("seeking", throttle(() => {
          this.emit(this.baseEvent("seek", { to: Number(this.video.currentTime) || 0 }));
        }, 1000));
  
        // Timeupdate is very chatty; throttle
        this.video.addEventListener("timeupdate", throttle(() => {
          this.emit(this.baseEvent("timeupdate"));
        }, 5000));
  
        document.addEventListener("visibilitychange", () => {
          this.emit(this.baseEvent("visibility", { state: document.visibilityState }));
        });
  
        window.addEventListener("beforeunload", () => {
          // best effort: flush queue & send a final ping
          const evt = this.baseEvent("unload");
          pushQueue(evt);
          flushQueue(this.opts.endpoint);
        });
      }
  
      async heartbeat() {
        const progress = this.progressPct();
        // Avoid noise if progress hasn’t changed at least 1%
        if (progress === this.lastHeartbeatProgress) return;
        this.lastHeartbeatProgress = progress;
        await this.emit(this.baseEvent("heartbeat"));
      }
  
      destroy() {
        clearInterval(this.heartbeatTimer);
      }
    }
  
    // ---- Public API (no panel)
    function initAnalytics(options = {}) {
      HIDE_EXISTING_TEST_UI(); // ensure no visible test UI remains
  
      // Locate main <video> on watch page
      const video =
        options.video ||
        document.querySelector("video#player, .watch-player video, video");
  
      if (!video) {
        // eslint-disable-next-line no-console
        console.warn("[LVS:analytics] No video element found.");
        return null;
      }
  
      const tracker = new Analytics(video, options);
  
      // If and only if ?analyticsTest=1, log extra diagnostics. No UI.
      if (TEST_MODE) {
        // eslint-disable-next-line no-console
        console.info("[LVS:analytics] TEST MODE enabled via URL (no panel shown).");
        window.__LVS_ANALYTICS_DEBUG__ = {
          tracker,
          flushQueue: () => flushQueue(tracker.opts.endpoint),
          queue: () => loadQueue(),
          clearQueue: () => saveQueue([]),
        };
      }
  
      return tracker;
    }
  
    // Expose globally
    window[NS] = {
      version: VERSION,
      init: initAnalytics,
      flush: () => flushQueue(DEFAULT_ENDPOINT),
    };
  
    // Auto-init on watch pages (safe no-op elsewhere)
    document.addEventListener("DOMContentLoaded", () => {
      // heuristic: only auto-init if a video exists on page
      const hasVideo = document.querySelector("video");
      if (hasVideo) {
        window[NS].init({
          // You can override the endpoint here if needed:
          // endpoint: "/api/analytics",
        });
      }
    });
  })();
  