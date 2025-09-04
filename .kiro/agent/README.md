# Agent Guidance: Local Video Server

## 🚨 CRITICAL: This is a FULLY WORKING APPLICATION

**Status: 100% UI Complete | Production Ready | Enhancement-Only Mode**

⚠️ **NEVER break existing functionality** — your role is to make **safe, incremental enhancements** that improve performance, UX, accessibility, and maintainability while preserving the working baseline.

---

## 📊 Project Status Overview

### ✅ Completed Features (100% Working)

- **UI System**: Complete glassmorphic/neomorphic design system with theme switching
- **Video Management**: Full video serving, metadata management, thumbnails
- **User Features**: Favorites, ratings, tagging, search, video previews
- **Accessibility**: WCAG AA compliant with high contrast mode, keyboard navigation
- **Cross-Platform**: Desktop, mobile, tablet, VR (Meta Quest) tested and working
- **Performance**: Optimized caching, lazy loading, adaptive streaming ready
- **Database**: SQLite with JSON fallback, migration system in place

### 🔧 Current Tech Stack

- **Backend**: Flask (migrating to FastAPI) + Python 3.13+
- **Frontend**: Vanilla JS + HTML/CSS (glassmorphic/neomorphic themes)
- **Database**: SQLite (`video_metadata.db`, `video_cache.db`) + JSON sidecars
- **Media**: FFmpeg integration, thumbnail generation, adaptive streaming
- **Deployment**: Local HTTPS, Windows primary/Linux secondary
- **Performance**: 50GB cache limit, streaming ladder 240p-4K

---

## 🎯 Enhancement-Only Approach

### ✅ SAFE Enhancement Categories

- **Performance Optimization**: Caching improvements, query optimization, memory management
- **UX Polish**: Animation refinements, accessibility improvements, mobile optimizations
- **Feature Extensions**: New filters, enhanced search, additional metadata fields
- **Code Quality**: Refactoring for maintainability, adding tests, documentation
- **Security**: Input validation, sanitization, secure headers

### ❌ FORBIDDEN Changes

- **Breaking Changes**: Removing working endpoints, changing API contracts
- **Architecture Rewrites**: Complete framework changes, database schema breaking changes
- **Dependency Conflicts**: Adding packages that conflict with current stack
- **UI Overhauls**: Removing working themes or breaking responsive design
- **Data Loss**: Any changes that could corrupt or lose user data

---

## 🛡️ Safety Framework

### Pre-Enhancement Checklist

1. **Verify Current State**: Confirm feature is working before changes
2. **Check Dependencies**: Ensure changes don't break existing integrations
3. **Test Backwards Compatibility**: Maintain all existing interfaces
4. **Performance Impact**: Measure before/after performance metrics
5. **Rollback Plan**: Have clear procedure to undo changes

### Critical Constraints

- **Windows Primary**: Optimize for Windows, ensure Linux compatibility
- **Local HTTPS**: Maintain self-signed certificate support
- **Cache Limits**: Respect 50GB cache maximum
- **Touch Targets**: Maintain 44px minimum touch targets
- **Theme System**: Preserve all 4 themes (default, glassmorphic, neomorphic, hybrid)

---

## 🚀 Focus Areas for Enhancement

### 1. Performance Optimization

- Database query optimization (maintain SQLite compatibility)
- Caching strategy improvements (respect 50GB limit)
- Memory usage optimization
- Streaming latency reduction

### 2. User Experience Polish

- Animation smoothness improvements
- Mobile/tablet experience refinements
- VR interaction enhancements
- Accessibility feature additions

### 3. Feature Extensions

- Enhanced search capabilities
- Additional metadata fields
- New filtering options
- Improved video preview system

### 4. Code Quality & Maintainability

- Code refactoring (preserve functionality)
- Test coverage improvements
- Documentation enhancements
- Error handling improvements

---

## 📋 Development Guidelines

### Code Standards

- **Python**: PEP8, black formatting, type hints
- **JavaScript**: ES6+, consistent naming, performance-focused
- **CSS**: BEM methodology, maintain theme architecture
- **Commits**: Conventional Commits format

### Testing Requirements

- Test existing functionality before changes
- Add tests for new features
- Validate cross-platform compatibility
- Performance regression testing

### Documentation

- Update relevant docs for any changes
- Maintain API documentation
- Keep README files current
- Document performance impacts

---

## 🔍 Quick Reference

### Key Files

- `main.py`: Flask server entry point
- `cache_manager.py`: Performance caching system
- `thumbnail_manager.py`: Video thumbnail generation
- `static/theme-manager.js`: Theme switching system
- `templates/`: HTML templates (working UI)

### Databases

- `video_metadata.db`: Video information, tags, ratings
- `video_cache.db`: Performance caching data
- JSON sidecars: Fallback data storage

### Performance Targets

- Page load: < 2 seconds
- Video preview start: < 500ms
- Theme switching: < 100ms
- Memory usage: < 1GB typical

---

## 🆘 When to Stop and Ask

**STOP and ask for clarification if you encounter:**

- Changes that might break existing functionality
- Database schema modifications
- Major dependency updates
- Architecture changes
- Performance regressions
- Accessibility compliance concerns

**Remember**: Your goal is to make the working application **better**, not different. Every change should add value while preserving the solid foundation that already exists.

---

*Last Updated: Based on Implementation Guide showing 100% UI completion and full feature set*
