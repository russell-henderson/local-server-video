"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  Bell,
  Cpu,
  Database,
  Image as ImageIcon,
  Link,
  ListChecks,
  Moon,
  MonitorSmartphone,
  Search,
  Server,
  Video,
} from "lucide-react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  fetchPerformanceSnapshot,
  fetchRouteMetrics,
  fetchStorageStats,
  fetchWorkerMetrics,
  fetchPopularTags,
  fetchActiveStreams,
  fetchCacheStatus,
  type PerformanceSnapshot,
  type RouteMetric,
  type StorageStats,
  type WorkerMetrics,
} from "@/lib/api";

const cards = [
  {
    title: "Active Streams",
    value: "––",
    hint: "Live pulls from video-server",
    icon: Activity,
    gradient: "bg-brand-cyan",
  },
  {
    title: "Storage",
    value: "Preparing",
    hint: "videos / images / system",
    icon: Database,
    gradient: "bg-brand-purple",
  },
  {
    title: "System Health",
    value: "Monitoring",
    hint: "CPU / RAM / queues",
    icon: Cpu,
    gradient: "bg-brand-orange",
  },
  {
    title: "Link Sentinel",
    value: "Idle",
    hint: "Dead link checks queued",
    icon: Server,
    gradient: "bg-brand-green",
  },
];

export default function Home() {
  const [mounted, setMounted] = useState(false);
  const [chartsReady, setChartsReady] = useState(false);
  useEffect(() => {
    setMounted(true);
    requestAnimationFrame(() => setChartsReady(true));
  }, []);

  const uploads = [
    { title: "Azure Night City", views: "1.2k", freshness: "2h ago" },
    { title: "Glass Tunnel Run", views: "980", freshness: "6h ago" },
    { title: "Neon Bokeh Study", views: "870", freshness: "1d ago" },
  ];

  const streams = [
    { user: "vr-proxy-12", path: "/watch/skyline", latency: "42ms" },
    { user: "edge-node-03", path: "/watch/midnight", latency: "57ms" },
    { user: "lan-admin", path: "/watch/drift", latency: "38ms" },
  ];

  const storageBreakdown = [
    { name: "Videos", value: 62, fill: "url(#brandCyan)" },
    { name: "Images", value: 18, fill: "url(#brandPurple)" },
    { name: "System", value: 20, fill: "url(#brandOrange)" },
  ];

  const bingeList = [
    { title: "Night Shift Drift", pct: 82 },
    { title: "Laser Alley Run", pct: 71 },
    { title: "Skyline Loop", pct: 65 },
    { title: "Chrome Bloom", pct: 59 },
  ];

  const tagCloud = [
    { label: "#cyber", weight: 32 },
    { label: "#night", weight: 26 },
    { label: "#city", weight: 20 },
    { label: "#drift", weight: 18 },
    { label: "#glass", weight: 14 },
  ];

  const [perf, setPerf] = useState<PerformanceSnapshot | null>(null);
  const [storage, setStorage] = useState<StorageStats | null>(null);
  const [routes, setRoutes] = useState<RouteMetric[]>([]);
  const [workers, setWorkers] = useState<WorkerMetrics | null>(null);
  const [pulseHistory, setPulseHistory] = useState<
    { time: string; rpm: number; p95: number; hour: string }[]
  >([]);
  const [popularTags, setPopularTags] = useState<string[]>([]);
  const [activeStreams, setActiveStreams] = useState<{ active_count: number; streams: any[] }>({
    active_count: 0,
    streams: [],
  });
  const [cacheStatus, setCacheStatus] = useState<any>(null);

  useEffect(() => {
    let mounted = true;
    const loadPerf = async () => {
      const data = await fetchPerformanceSnapshot();
      if (mounted) {
        setPerf(data);
        if (data?.generated_at) {
          const dt = new Date(data.generated_at);
          const label = dt.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
          const hour = dt.toLocaleTimeString([], { hour: "2-digit", hour12: false });
          const rpm = data.global?.request_count
            ? (data.global.request_count / (data.window_seconds || 900)) * 60
            : 0;
          setPulseHistory((prev) => {
            const next = [
              ...prev,
              {
                time: label,
                rpm,
                p95: data.global?.p95_latency_ms ?? 0,
                hour,
              },
            ];
            return next.slice(-24); // keep last 24 samples
          });
        }
      }
    };
    const loadStorage = async () => {
      const data = await fetchStorageStats();
      if (mounted) setStorage(data);
    };
    const loadRoutes = async () => {
      const data = await fetchRouteMetrics();
      if (mounted) setRoutes(data);
    };
    const loadWorkers = async () => {
      const data = await fetchWorkerMetrics();
      if (mounted) setWorkers(data);
    };
    const loadTags = async () => {
      const data = await fetchPopularTags();
      if (mounted) setPopularTags(data);
    };
    const loadActive = async () => {
      const data = await fetchActiveStreams();
      if (mounted) setActiveStreams(data);
    };
    const loadCache = async () => {
      const data = await fetchCacheStatus();
      if (mounted) setCacheStatus(data);
    };
    loadPerf();
    loadStorage();
    loadRoutes();
    loadWorkers();
    loadTags();
    loadActive();
    loadCache();
    const perfInterval = setInterval(loadPerf, 10000);
    const routesInterval = setInterval(loadRoutes, 15000);
    const workerInterval = setInterval(loadWorkers, 20000);
    const tagsInterval = setInterval(loadTags, 60000);
    const activeInterval = setInterval(loadActive, 10000);
    const cacheInterval = setInterval(loadCache, 60000);
    return () => {
      mounted = false;
      clearInterval(perfInterval);
      clearInterval(routesInterval);
      clearInterval(workerInterval);
      clearInterval(tagsInterval);
      clearInterval(activeInterval);
      clearInterval(cacheInterval);
    };
  }, []);

  const storageSeries = useMemo(() => {
    if (!storage) return storageBreakdown;
    const total = storage.total_bytes || 1;
    const used = storage.used_bytes ?? storage.videos_bytes + storage.images_bytes;
    const free = Math.max(0, total - used);
    const other = Math.max(0, used - storage.videos_bytes - storage.images_bytes);
    return [
      { name: "Videos", value: Math.round((storage.videos_bytes / total) * 100), fill: "url(#brandCyan)" },
      { name: "Images", value: Math.round((storage.images_bytes / total) * 100), fill: "url(#brandPurple)" },
      { name: "Other", value: Math.max(0, Math.round((other / total) * 100)), fill: "url(#brandOrange)" },
      { name: "Free", value: Math.max(0, Math.round((free / total) * 100)), fill: "url(#brandGreen)" },
    ].filter((seg) => seg.value > 0);
  }, [storage]);

  const storageLegend = useMemo(() => {
    if (!storage) return [];
    const total = storage.total_bytes || 1;
    const entries = [
      { label: "Videos", bytes: storage.videos_bytes, color: "bg-cyan" },
      { label: "Images", bytes: storage.images_bytes, color: "bg-purple" },
      { label: "Other", bytes: Math.max(0, storage.used_bytes ?? 0 - (storage.videos_bytes + storage.images_bytes)), color: "bg-orange-400" },
    ];
    const freeBytes = Math.max(0, (storage.free_bytes ?? 0));
    entries.push({ label: "Free", bytes: freeBytes, color: "bg-emerald-400" });
    return entries.map((e) => ({
      ...e,
      pct: Math.max(0, Math.min(100, (e.bytes / total) * 100)),
      human: `${(e.bytes / 1_073_741_824).toFixed(1)} GB`,
    }));
  }, [storage]);

  const pulseData = useMemo(() => {
    return pulseHistory.length
      ? pulseHistory.map((p) => ({ time: p.time, viewers: p.rpm, bitrate: p.p95 }))
      : [
          { time: "00:00", viewers: 12, bitrate: 180 },
          { time: "04:00", viewers: 18, bitrate: 210 },
          { time: "08:00", viewers: 26, bitrate: 260 },
          { time: "12:00", viewers: 34, bitrate: 320 },
          { time: "16:00", viewers: 48, bitrate: 410 },
          { time: "20:00", viewers: 42, bitrate: 360 },
          { time: "23:00", viewers: 30, bitrate: 290 },
        ];
  }, [pulseHistory]);

  const goldenHour = useMemo(() => {
    if (!pulseHistory.length) {
      return [
        { hour: "00", hits: 8 },
        { hour: "04", hits: 12 },
        { hour: "08", hits: 28 },
        { hour: "12", hits: 36 },
        { hour: "16", hits: 48 },
        { hour: "20", hits: 42 },
      ];
    }
    const buckets: Record<string, number> = {};
    pulseHistory.forEach((p) => {
      buckets[p.hour] = (buckets[p.hour] || 0) + p.rpm;
    });
    return Object.entries(buckets)
      .sort(([a], [b]) => Number(a) - Number(b))
      .map(([hour, hits]) => ({ hour, hits }));
  }, [pulseHistory]);

  const streamCount = useMemo(() => {
    if (activeStreams.active_count) {
      return `${activeStreams.active_count} now playing`;
    }
    if (!routes.length) return perf?.global?.request_count ?? "--";
    const total = routes
      .filter((r) => r.path.includes("/watch") || r.path.includes("/video"))
      .reduce((sum, r) => sum + (r.request_count || 0), 0);
    return `${total} req (last 15m)`;
  }, [routes, perf, activeStreams]);

  const kpiValues = {
    streams: streamCount,
    storage: storage ? `${(storage.total_bytes / 1_073_741_824).toFixed(1)} GB` : "Prep",
    health: perf?.status?.overall ?? "unknown",
    sentinel: "Idle",
    p95: perf?.global?.p95_latency_ms ?? null,
    errorRate: perf ? perf.global.error_rate * 100 : null,
    ratingsP95: perf?.ratings?.p95_latency_ms ?? null,
    cacheUsage: perf?.cache?.preview_cache_usage_ratio,
  };

  return (
    <div className="min-h-screen w-full" suppressHydrationWarning>
      <div className="grid min-h-screen grid-cols-[240px_1fr] gap-6 px-6 py-8 md:grid-cols-[260px_1fr] md:px-8">
        {/* Sidebar */}
        <aside className="glass flex h-full flex-col rounded-2xl p-5 shadow-neon">
          <div className="mb-8">
            <div className="text-xs uppercase tracking-[0.3em] text-cyan/80">Admin</div>
            <div className="text-2xl font-semibold text-white">Neon Control</div>
            <div className="text-sm text-slate-400">Netflix-Studio style shell</div>
          </div>
          <nav className="space-y-2">
            {[
              { label: "Dashboard", icon: MonitorSmartphone, href: "/" },
              { label: "Video Library", icon: Video, href: `${process.env.NEXT_PUBLIC_VIDEO_SERVER_URL || "http://localhost:5000"}/` },
              { label: "Image Groups", icon: ImageIcon, href: `${process.env.NEXT_PUBLIC_VIDEO_SERVER_URL || "http://localhost:5000"}/gallery` },
              { label: "Links", icon: Link, href: `${process.env.NEXT_PUBLIC_VIDEO_SERVER_URL || "http://localhost:5000"}/links` },
              { label: "System Health", icon: ListChecks, href: `${process.env.NEXT_PUBLIC_VIDEO_SERVER_URL || "http://localhost:5000"}/admin/performance` },
            ].map((item, idx) => {
              const Icon = item.icon;
              const active = idx === 0;
              return (
                <a
                  key={item.label}
                  href={item.href}
                  target={item.href.startsWith("http") ? "_blank" : undefined}
                  rel="noreferrer"
                  className={`flex w-full items-center gap-3 rounded-xl px-3 py-3 text-left text-sm font-semibold transition ${
                    active
                      ? "bg-ink-glow/70 text-white shadow-neon"
                      : "text-slate-300 hover:bg-ink-glow/40"
                  }`}
                >
                  <Icon className="h-4 w-4 text-cyan" />
                  <span>{item.label}</span>
                </a>
              );
            })}
          </nav>
          <div className="mt-auto rounded-xl border border-border/60 bg-ink-glow/60 p-4 text-sm text-slate-200">
            <div className="flex items-center gap-3">
              <span className="h-2 w-2 animate-pulse rounded-full bg-green-400 drop-shadow-glow" />
              <div>
                <div className="font-semibold">Cluster Online</div>
                <div className="text-slate-400">video-server · admin-dashboard</div>
              </div>
            </div>
          </div>
        </aside>

        {/* Main */}
        <main className="neon-plate relative rounded-2xl shadow-neon">
          <div className="grid-overlay pointer-events-none absolute inset-0" />
          <div className="relative flex h-full flex-col gap-6 p-6 md:p-8">
            {/* Top bar */}
            <header className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.25em] text-cyan/80">Phase 2</p>
                <h1 className="text-3xl font-semibold text-white md:text-4xl">
                  Netflix-Studio Ops Hub
                </h1>
                <p className="text-sm text-slate-300">
                  Sidebar + topbar shell · Grid rows for KPIs, charts, and tables.
                </p>
              </div>
              <div className="flex flex-col gap-3 md:flex-row md:items-center">
                <div className="flex items-center gap-2 rounded-xl border border-border/60 bg-ink-glow/60 px-3 py-2">
                  <Search className="h-4 w-4 text-cyan" />
                  <input
                    className="w-48 bg-transparent text-sm text-white outline-none placeholder:text-slate-500"
                    placeholder="Global search"
                  />
                </div>
                <button className="flex items-center gap-2 rounded-xl border border-border/60 bg-ink-glow/80 px-4 py-2 text-sm font-semibold text-white shadow-neon">
                  <Bell className="h-4 w-4 text-cyan" />
                  Alerts
                </button>
              </div>
            </header>

            {/* Row 1: KPIs */}
            <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              {[
                { title: "Active Streams", value: kpiValues.streams, hint: "Requests to /watch,/video in last 15m", icon: Activity, gradient: "bg-brand-cyan" },
                {
                  title: "Storage",
                  value: kpiValues.storage,
                  hint: "videos + images mounted",
                  icon: Database,
                  gradient: "bg-brand-purple",
                },
                {
                  title: "Health",
                  value: kpiValues.health,
                  hint: `Global p95 ${kpiValues.p95 ? `${kpiValues.p95.toFixed(1)}ms` : "--"} · Error ${kpiValues.errorRate ? `${kpiValues.errorRate.toFixed(2)}%` : "--"}`,
                  icon: Cpu,
                  gradient: "bg-brand-orange",
                },
                {
                  title: "Link Sentinel",
                  value: kpiValues.sentinel,
                  hint: "Dead link checks queued",
                  icon: Server,
                  gradient: "bg-brand-green",
                },
              ].map((card) => {
                const Icon = card.icon;
                return (
                  <div key={card.title} className="glass rounded-xl border border-border/60">
                    <div className={`h-1.5 w-full rounded-t-xl ${card.gradient}`} />
                    <div className="flex items-start gap-3 px-4 py-4">
                      <div className="rounded-lg bg-ink-glow/60 p-2">
                        <Icon className="h-5 w-5 text-slate-100" strokeWidth={1.75} />
                      </div>
                      <div className="space-y-1">
                        <p className="text-sm uppercase tracking-[0.15em] text-slate-400">
                          {card.title}
                        </p>
                        <p className="text-2xl font-semibold text-white">{card.value}</p>
                        <p className="text-xs text-slate-400">{card.hint}</p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </section>

            {/* Row 2: split cards + big chart */}
            <section className="grid gap-4 xl:grid-cols-[1.1fr_1.1fr_1.8fr]">
              <div className="glass rounded-xl border border-border/60 p-5">
                <h2 className="text-lg font-semibold text-white">Storage Real Estate</h2>
                <p className="text-sm text-slate-300">
                  Videos vs images vs free space from mounted volumes (videos/images).
                </p>
                <div className="mt-4 h-48 w-full min-h-[200px] min-w-[280px]">
                  {chartsReady && storageSeries.length ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <defs>
                          <linearGradient id="brandCyan" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#22d3ee" stopOpacity={0.9} />
                            <stop offset="100%" stopColor="#2563eb" stopOpacity={0.7} />
                          </linearGradient>
                          <linearGradient id="brandPurple" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#a855f7" stopOpacity={0.9} />
                            <stop offset="100%" stopColor="#ec4899" stopOpacity={0.7} />
                          </linearGradient>
                          <linearGradient id="brandOrange" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#fb923c" stopOpacity={0.9} />
                            <stop offset="100%" stopColor="#ef4444" stopOpacity={0.7} />
                          </linearGradient>
                          <linearGradient id="brandGreen" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#34d399" stopOpacity={0.9} />
                            <stop offset="100%" stopColor="#14b8a6" stopOpacity={0.7} />
                          </linearGradient>
                        </defs>
                        <Pie
                          data={storageSeries}
                          dataKey="value"
                          nameKey="name"
                          cx="50%"
                          cy="50%"
                          innerRadius={40}
                          outerRadius={70}
                          stroke="rgba(255,255,255,0.08)"
                          strokeWidth={2}
                        >
                          {storageBreakdown.map((entry, idx) => (
                            <Cell key={`cell-${idx}`} fill={entry.fill} />
                          ))}
                        </Pie>
                        <Tooltip
                          contentStyle={{ backgroundColor: "#0f172a", border: "1px solid #22d3ee" }}
                          labelStyle={{ color: "#e2e8f0" }}
                          formatter={(value: number, name: string) => [`${value}%`, name]}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-full w-full rounded-lg bg-ink-glow/60" />
                  )}
                </div>
                <div className="mt-3 grid grid-cols-1 gap-2 text-sm text-slate-200 md:grid-cols-2">
                  {storageLegend.map((item) => (
                    <div key={item.label} className="flex items-center justify-between rounded-lg bg-ink-glow/50 px-3 py-2">
                      <div className="flex items-center gap-2">
                        <span className={`h-2.5 w-2.5 rounded-full ${item.color}`} />
                        <span>{item.label}</span>
                      </div>
                      <div className="text-xs text-slate-300">{item.human} · {item.pct.toFixed(1)}%</div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="glass rounded-xl border border-border/60 p-5">
                <h2 className="text-lg font-semibold text-white">Link Sentinel</h2>
                <p className="text-sm text-slate-300">
                  Dead-link checks stub. Needs backend probe to crawl bookmarks/gallery/embeds.
                </p>
                <div className="mt-4 flex flex-col gap-3">
                  <div className="flex items-center gap-3 rounded-lg bg-ink-glow/60 p-3">
                    <span className="h-2 w-2 rounded-full bg-orange-300 drop-shadow-glow" />
                    <div className="text-sm text-slate-200">
                      <div className="font-semibold">Awaiting crawl</div>
                      <div className="text-slate-400">Targets: bookmarks, gallery, embeds</div>
                    </div>
                  </div>
                  {cacheStatus && (
                    <div className="rounded-lg bg-ink-glow/60 p-3 text-sm text-slate-200">
                      <div className="font-semibold">Cache Status</div>
                      <div className="text-xs text-slate-400">Preview cache usage</div>
                      <div className="mt-1 text-xs">
                        {cacheStatus.preview_cache_items ?? 0} items ·{" "}
                        {(cacheStatus.preview_cache_usage_ratio
                          ? cacheStatus.preview_cache_usage_ratio * 100
                          : 0
                        ).toFixed(2)}
                        % of {((cacheStatus.preview_cache_limit_bytes ?? 0) / 1_073_741_824).toFixed(1)} GB
                      </div>
                    </div>
                  )}
                </div>
              </div>

              <div className="glass rounded-xl border border-border/60 p-5">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-lg font-semibold text-white">Pulse · Realtime Traffic</h2>
                <p className="text-sm text-slate-300">
                  Requests per minute from perf snapshots (10s polling).
                </p>
              </div>
              <div className="rounded-full bg-ink-glow/70 px-3 py-1 text-xs text-cyan">
                Live
              </div>
            </div>
                <div className="mt-4 h-56 w-full min-h-[220px] min-w-[320px]">
                  {chartsReady && pulseData.length ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={pulseData}>
                        <defs>
                          <linearGradient id="colorViewers" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#22d3ee" stopOpacity={0.6} />
                            <stop offset="95%" stopColor="#22d3ee" stopOpacity={0.05} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid stroke="rgba(148,163,184,0.15)" vertical={false} />
                        <XAxis dataKey="time" stroke="#94a3b8" />
                        <YAxis stroke="#94a3b8" />
                        <Tooltip
                          contentStyle={{ backgroundColor: "#0f172a", border: "1px solid #2563eb" }}
                          labelStyle={{ color: "#e2e8f0" }}
                        />
                        <Area
                          type="monotone"
                          dataKey="viewers"
                          stroke="#22d3ee"
                          strokeWidth={2}
                          fill="url(#colorViewers)"
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-full w-full rounded-lg bg-ink-glow/60" />
                  )}
                </div>
              </div>
            </section>

            {/* Row 3: tables */}
            <section className="grid gap-4 lg:grid-cols-2">
              <div className="glass rounded-xl border border-border/60 p-5">
                <h2 className="text-lg font-semibold text-white">Route Performance (p95)</h2>
                <p className="text-sm text-slate-300">Top endpoints by p95 latency (last 15m). Suggestions highlight slow/erroring routes.</p>
                <div className="mt-4 space-y-3 text-sm text-slate-200">
                  {(routes.length ? routes.slice(0, 6) : []).map((item) => {
                    const errPct = (item.error_rate * 100).toFixed(2);
                    let tip = "";
                    if (item.p95_latency_ms > 500) tip = "Investigate DB/cache or reduce payload size.";
                    else if (item.error_rate > 0.02) tip = "Check logs for 5xx; add retries/backoff.";
                    else if (item.request_count < 5) tip = "Low volume; watch for spikes.";
                    return (
                      <div
                        key={`${item.method}-${item.path}`}
                        className="rounded-lg bg-ink-glow/60 px-3 py-2"
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="font-semibold">{item.path}</div>
                            <div className="text-xs text-slate-400">
                              {item.method} · {item.request_count} req · err {errPct}%
                            </div>
                          </div>
                          <div className="text-cyan font-semibold">{item.p95_latency_ms.toFixed(1)} ms</div>
                        </div>
                        {tip && <div className="mt-1 text-xs text-orange-300">Tip: {tip}</div>}
                      </div>
                    );
                  })}
                  {!routes.length && (
                    <div className="rounded-lg bg-ink-glow/60 px-3 py-2 text-xs text-slate-400">
                      Awaiting route metrics...
                    </div>
                  )}
                </div>
              </div>

              <div className="glass rounded-xl border border-border/60 p-5">
                <h2 className="text-lg font-semibold text-white">Workers / Queues</h2>
                <p className="text-sm text-slate-300">Live worker snapshot from video-server.</p>
                <div className="mt-4 space-y-3 text-sm text-slate-200">
                  {workers?.queues?.length ? (
                    workers.queues.map((q) => (
                      <div
                        key={q.name}
                        className="flex items-center justify-between rounded-lg bg-ink-glow/60 px-3 py-2"
                      >
                        <div>
                          <div className="font-semibold">{q.name}</div>
                          <div className="text-xs text-slate-400">
                            pending {q.pending_jobs} · running {q.in_progress_jobs} · failed {q.failed_jobs}
                          </div>
                        </div>
                        <span className="text-cyan font-semibold">{q.status}</span>
                      </div>
                    ))
                  ) : (
                    <div className="rounded-lg bg-ink-glow/60 px-3 py-2 text-xs text-slate-400">
                      Workers disabled or no queues reported.
                    </div>
                  )}
                </div>
              </div>

              <div className="glass rounded-xl border border-border/60 p-5">
                <h2 className="text-lg font-semibold text-white">Now Playing</h2>
                <p className="text-sm text-slate-300">Recent /watch,/video requests (last 5 min).</p>
                <div className="mt-4 space-y-3 text-sm text-slate-200">
                  {activeStreams.streams.length ? (
                    activeStreams.streams.map((s, idx) => (
                      <div
                        key={`${s.path}-${idx}`}
                        className="flex items-center justify-between rounded-lg bg-ink-glow/60 px-3 py-2"
                      >
                        <div>
                          <div className="font-semibold truncate max-w-xs">
                            {s.path?.split("/").pop() || s.path}
                          </div>
                          <div className="text-xs text-slate-400">
                            {s.method} · last seen {Math.round(s.last_seen_seconds_ago)}s ago
                          </div>
                        </div>
                        <div className="text-xs text-cyan">{s.remote_addr || "local"}</div>
                      </div>
                    ))
                  ) : (
                    <div className="rounded-lg bg-ink-glow/60 px-3 py-2 text-xs text-slate-400">
                      No active streams detected in the last 5 minutes.
                    </div>
                  )}
                </div>
              </div>
            </section>

            {/* Row 4: engagement + tag cloud */}
            <section className="grid gap-4 xl:grid-cols-[1.3fr_1fr]">
              <div className="glass rounded-xl border border-border/60 p-5">
                <h2 className="text-lg font-semibold text-white">Golden Hour · Access Density</h2>
                <p className="text-sm text-slate-300">
                  Requests binned by hour (live perf snapshots). Populates as samples arrive.
                </p>
                <div className="mt-4 h-48 w-full min-h-[200px] min-w-[320px]">
                  {chartsReady && goldenHour.length ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={goldenHour} barSize={24}>
                        <CartesianGrid stroke="rgba(148,163,184,0.15)" vertical={false} />
                        <XAxis dataKey="hour" stroke="#94a3b8" />
                        <YAxis stroke="#94a3b8" />
                        <Tooltip
                          contentStyle={{ backgroundColor: "#0f172a", border: "1px solid #2563eb" }}
                          labelStyle={{ color: "#e2e8f0" }}
                        />
                        <Bar dataKey="hits" radius={[6, 6, 0, 0]} fill="url(#brandCyan)" />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-full w-full rounded-lg bg-ink-glow/60" />
                  )}
                </div>
              </div>

              <div className="glass rounded-xl border border-border/60 p-5">
                <h2 className="text-lg font-semibold text-white">Engagement & Tags</h2>
                <p className="text-sm text-slate-300">Live tag cloud (popular tags API) and placeholder binge list.</p>
                <div className="mt-4 space-y-4">
                  <div>
                    <div className="text-xs uppercase tracking-[0.2em] text-slate-400">Binge-Worthy</div>
                    <div className="mt-2 space-y-2">
                      {bingeList.map((item) => (
                        <div key={item.title} className="rounded-lg bg-ink-glow/60 px-3 py-2">
                          <div className="flex items-center justify-between text-sm text-slate-100">
                            <span>{item.title}</span>
                            <span className="text-cyan">{item.pct}%</span>
                          </div>
                          <div className="mt-1 h-2 rounded-full bg-ink-glow/80">
                            <div
                              className="h-2 rounded-full bg-brand-purple"
                              style={{ width: `${item.pct}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs uppercase tracking-[0.2em] text-slate-400">Tag Cloud</div>
                    <div className="mt-2 flex flex-wrap gap-2 text-sm">
                      {(popularTags.length ? popularTags : tagCloud.map((t) => t.label)).map((tag, idx) => {
                        const raw =
                          typeof tag === "string"
                            ? tag
                            : (tag as any)?.tag ?? (tag as any)?.label ?? String(tag ?? "");
                        const clean = raw.replace?.(/^#/, "") ?? String(raw);
                        return (
                          <span
                            key={`${clean}-${idx}`}
                            className="rounded-full border border-border/60 bg-ink-glow/70 px-3 py-1 text-slate-100 shadow-neon"
                            style={{ fontSize: `${12 + Math.max(1, 20 - idx) * 0.2}px` }}
                          >
                            #{clean}
                          </span>
                        );
                      })}
                    </div>
                  </div>
                </div>
              </div>
            </section>
          </div>
        </main>
      </div>
    </div>
  );
}
