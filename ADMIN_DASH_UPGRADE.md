# ADMIN_DASH_UPGRADE.md

## 🚀 Project Overview

**Objective:** Replace the legacy, text-heavy system dashboard with a high-fidelity, "Netflix-Studio-style" analytics hub.
**Target Aesthetic:** Dark mode, neon gradients, glassmorphism, high contrast.
**Core Stack:** Docker, React/Next.js (Recommended), Tailwind CSS, Recharts (for data viz).

---

## 📋 Phase 1: Environment & Architecture

### 1.1 Infrastructure Setup

- [ ] **Initialize New Dashboard Container**
  - Create a new `Dockerfile` for the dashboard frontend (Node/React).
  - Update `docker-compose.yml` to include the `admin-dashboard` service.
  - Ensure networking allows `admin-dashboard` to talk to the `video-server` and `database` containers.
- [ ] **Data Pipeline Strategy**
  - [ ] Identify data sources:
    - **Logs:** Map volume `./logs:/app/logs` to parse access logs (for traffic/views).
    - **Database:** Connect to the metadata DB (SQLite/MySQL) for video titles, tags, and link status.
    - **System:** Mount `/proc` or use a node exporter for CPU/Ram (if "Transcoding Queue" requires hardware stats).

### 1.2 Design System (The "Look")

- [ ] **Install Dependencies**
  - Install `tailwindcss` and `headlessui` (or similar).
  - Install `recharts` or `chart.js` for the graphs.
  - Install `lucide-react` or `heroicons` for the UI icons.
- [ ] **Define Color Palette (Neon/Dark)**
  - Background: `#0f172a` (Slate 900) or pure black `#000000`.
  - Card BG: Semi-transparent with blur (`bg-slate-800/50 backdrop-blur-md`).
  - Gradients: Define 4 core gradients in `tailwind.config.js`:
    - `brand-cyan`: `from-cyan-400 to-blue-600`
    - `brand-purple`: `from-purple-500 to-pink-500`
    - `brand-orange`: `from-orange-400 to-red-500`
    - `brand-green`: `from-emerald-400 to-teal-600`

---

## 🎨 Phase 2: UI Components & Layout

### 2.1 The Shell

- [ ] **Sidebar Navigation**
  - Fixed left sidebar.
  - Sections: Dashboard, Video Library, Image Groups, Links, System Health.
  - Active state: Glow effect + gradient text.
- [ ] **Top Bar**
  - Search bar (Global search).
  - User profile/Admin toggle.
  - Notification bell (for "Dead Link" alerts).

### 2.2 Dashboard Grid Layout

- [ ] Create a responsive CSS Grid layout.
- [ ] **Row 1:** 4 Key Metric Cards (Gradient Headers).
- [ ] **Row 2:** 2 Medium Split Cards + 1 Large Chart Area.
- [ ] **Row 3:** Data Tables (Recent Uploads/Active Streams).

---

## ⚡ Phase 3: Core Feature Implementation

*Implement the following modular widgets based on the 12-point capability list.*

### 3.1 High-Priority Widgets (Traffic & Content)

- [ ] **The "Pulse" (Real-Time Traffic)**
  - *UI:* Large Area Chart (Bottom of dashboard).
  - *Data:* Websocket connection or polling active server connections.
  - *Tooltip:* Hovering shows specific video titles being streamed.
- [ ] **Storage "Real Estate" Visualizer**
  - *UI:* Donut Chart or Stacked Bar.
  - *Logic:* Calculate total size of `./videos` vs `./images` vs `./system`.
  - *Addon:* "Projected Fill Date" calculation.
- [ ] **"Dead Link" Sentinel**
  - *UI:* Status Card (Green/Red indicator).
  - *Backend:* Cron job script to `curl` headers of all saved links.
  - *Action:* Return list of 4xx/5xx responses.

### 3.2 Engagement Widgets

- [ ] **"Binge-Worthy" Heatmap**
  - *UI:* List view with retention progress bars.
  - *Logic:* (Stream Duration / Video Duration) * 100.
- [ ] **"Golden Hour" Clock**
  - *UI:* Histogram Bar Chart (00:00 to 23:00).
  - *Data:* Aggregate historic access logs by hour.
- [ ] **Search Query Intelligence**
  - *UI:* Scrolling Ticker or "Top 5" list.
  - *Data:* Log search inputs from the main video interface.

### 3.3 Library Management Widgets

- [ ] **The "Tag Cloud" Sunburst**
  - *UI:* Visual bubble chart or colored tag cluster.
  - *Logic:* Count distinct tags in the DB and group by frequency.
- [ ] **"Dusty Shelf" Detector**
  - *UI:* Simple List of "Stale Content".
  - *Logic:* Query items with `last_viewed_date > 6 months` OR `views == 0`.
  - *Action:* "Shuffle to Front" button.
- [ ] **Gallery "Hotspots"**
  - *UI:* Card with thumbnail previews of popular image groups.
  - *Logic:* Most accessed folders in the image directory.

### 3.4 System & Admin Widgets

- [ ] **Transcoding Queue**
  - *UI:* Animated Progress Bar / "Engine Room" status.
  - *Data:* Check for active `ffmpeg` or transcoding processes in Docker.
- [ ] **"Popcorn" Meter (Quality Score)**
  - *UI:* Large Score Card.
  - *Logic:* Custom algorithm (e.g., `(Total Views / Total Content) * Retention Factor`).
- [ ] **Bandwidth "Cost" Calculator**
  - *UI:* Finance-style ticker.
  - *Logic:* `Total Bytes Sent * $0.09` (Simulated AWS cost).

## 🛠 Phase 4: API & Backend Requirements

### 4.1 API Routes (Node.js/Express or Next.js API)

- [ ] `GET /api/stats/realtime` - Active connections.
- [ ] `GET /api/content/stale` - Returns "Dusty Shelf" items.
- [ ] `GET /api/system/storage` - Returns disk usage JSON.
- [ ] `GET /api/links/health` - Triggers the Sentinel check.

### 4.2 Database Optimization

- [ ] Ensure video/image tables have a `last_accessed` and `view_count` column.
- [ ] Create an index on `tags` for the Sunburst widget performance.

## 🚀 Phase 5: Deployment

- [ ] **Docker Compose Finalization**
  - Map port `3000:3000` (or preferred port) for the dashboard.
  - Set environment variables for DB connection strings.
- [ ] **Testing**
  - Verify "Sentinel" doesn't block the main thread.
  - Verify "Pulse" graph updates without page refresh.
- [ ] **Launch**
  - `docker-compose up -d --build`

---

### 📝 Notes for Codex

- **Style Reference:** `original-9cd2c1d6...webp`
- **Legacy Reference:** `image_078401.png`
- **Constraint:** Must run locally within the existing Docker network.
- **Tone:** The UI must feel "premium" and "gamified," not utilitarian.
