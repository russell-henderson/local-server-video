# Local Video Server TODOs

Purpose: This file is the live, actionable task list for Local Video Server.  
All older planning docs listed in `docs/ARCHIVE_INDEX.md` are history only.

Long form roadmap and context lives in `TODOv4.md`.  
Use this file for what you are doing next, not for long essays.

---

## 1. Active epics

High level work areas that are currently in motion.

- [ ] Documentation consolidation and cleanup
- [ ] Admin dashboard implementation
- [ ] Performance and monitoring polish
- [ ] VR and device specific UX polish

Update this section when you start or finish a major area.

---

## 2. Current sprint tasks

Short, concrete items that you plan to work on next.

### 2.1 Documentation

- [ ] Confirm `DOCS_INVENTORY.md` matches actual files
- [ ] Keep `PERFORMANCE.md` in sync with real changes
- [ ] Keep `IMPLEMENTATION.md` in sync with real changes

### 2.2 Admin dashboard

- [ ] Implement `templates/admin/performance.html` layout according to `docs/ADMIN_DASHBOARD.md`
- [ ] Confirm `/admin/performance` renders KPI cards, summary panels, route table, and efficiency charts (placeholder data is acceptable at first)
- [ ] Wire `/admin/performance.json` to `PerformanceMetrics` using the schemas in `docs/PERFORMANCE_MONITORING.md`
- [ ] Implement the first real KPI card backed by live data from `/admin/performance.json`

### 2.3 Performance and monitoring

- [ ] Apply performance monitor decorator to key routes
- [ ] Wire metrics storage that matches `PERFORMANCE_MONITORING.md`
- [ ] Expose route metrics at `/api/admin/performance/routes`

Update these lists as you actually complete items. This file should always reflect reality.

---

## 3. Backlog

Things you want to do, but not active yet.

- [ ] Deeper VR specific dashboard views
- [ ] Additional analytics visualizations for tags and search
- [ ] More robust backup and restore tooling

Move items from here into the current sprint section when they become active.

---

## 4. References

Use these for context, not for new tasks.

- Long form roadmap: `TODOv4.md`
- Documentation inventory: `docs/DOCS_INVENTORY.md`
- Archive overview: `docs/ARCHIVE_INDEX.md`
- Performance strategy: `docs/PERFORMANCE.md`
- Implementation guide: `docs/IMPLEMENTATION.md`
- Admin dashboard spec: `docs/ADMIN_DASHBOARD.md`
- Metric schemas and monitoring: `docs/PERFORMANCE_MONITORING.md`
