# CODEX Trading System - Dashboard Visual Preview

## Overview

This document describes the visual appearance and layout of the new frontend dashboard at `http://localhost:8001/`.

## Layout Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                        HEADER SECTION                            │
│  ┌─────────────────────────────┐  ┌───────────────────────┐    │
│  │  CODEX Trading System [P5]  │  │ 🟢 OPERATIONAL         │    │
│  │  Phase 5 - Real-time...     │  └───────────────────────┘    │
│  └─────────────────────────────┘                                │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   QUICK ACTIONS (4 Buttons)                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────┐ │
│  │ 📖 API Docs │ │ 💓 Health   │ │ 📊 Dashboard│ │ 🔄 Refresh│ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └──────────┘ │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   SYSTEM METRICS (4 Cards)                       │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────┐│
│  │💼 Initial    │ │💼 Portfolio  │ │📚 Active     │ │📈 Total││
│  │   Capital    │ │   Value      │ │   Positions  │ │   Return││
│  │              │ │              │ │              │ │        ││
│  │ $1,000,000.00│ │ $1,050,000.00│ │      15      │ │ +5.00% ││
│  │              │ │              │ │              │ │        ││
│  │ Starting bal │ │ Current total│ │ Open trades  │ │Perform.││
│  └──────────────┘ └──────────────┘ └──────────────┘ └────────┘│
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   API ENDPOINTS (2 Panels)                       │
│  ┌─────────────────────────┐ ┌─────────────────────────────┐  │
│  │  🖥️ REST API Endpoints  │ │  🔌 WebSocket Endpoints     │  │
│  │                         │ │                             │  │
│  │  GET /api/trading/...   │ │  WS /ws/portfolio           │  │
│  │  GET /api/trading/...   │ │  WS /ws/performance         │  │
│  │  GET /api/risk/summary  │ │  WS /ws/risk                │  │
│  │  GET /api/system/status │ │  WS /ws/orders              │  │
│  │  GET /api/performance/..│ │  WS /ws/system              │  │
│  └─────────────────────────┘ └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   SYSTEM FEATURES (3 Cards)                      │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐   │
│  │🛡️ Risk Mgmt │ │📊 Performance│ │🤖 Automated Trading  │   │
│  │              │ │   Analytics  │ │                      │   │
│  │ Real-time    │ │ Comprehensive│ │ AI-powered strategy  │   │
│  │ position     │ │ performance  │ │ execution and        │   │
│  │ sizing...    │ │ metrics...   │ │ optimization         │   │
│  └──────────────┘ └──────────────┘ └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         FOOTER                                   │
│  CODEX Trading System v1.0.0 | Phase 5 - Real-time Trading     │
│  Last Updated: 2025-10-25 11:30:45                              │
└─────────────────────────────────────────────────────────────────┘
```

## Color Palette

### Background
- **Main Background**: Linear gradient from `#0f172a` (dark slate) to `#1e293b` (slate)
- **Card Background**: `rgba(30, 41, 59, 0.7)` with backdrop blur (glass morphism)
- **Hover Cards**: Blue glow shadow `rgba(59, 130, 246, 0.2)`

### Text Colors
- **Primary Text**: `#f1f5f9` (gray-100) - White-ish
- **Secondary Text**: `#94a3b8` (gray-400) - Light gray
- **Tertiary Text**: `#64748b` (gray-500) - Medium gray

### Accent Colors
- **Blue (Primary)**: `#3b82f6` (buttons, links, borders)
- **Cyan (Secondary)**: `#06b6d4` (title gradient)
- **Green (Success)**: `#10b981` (positive returns, operational status)
- **Red (Error)**: `#ef4444` (negative returns, errors)
- **Yellow (Warning)**: `#f59e0b` (degraded status)

### Icon Colors (Font Awesome)
- Wallet: Blue `#3b82f6`
- Briefcase: Green `#10b981`
- Layer-group: Yellow `#f59e0b`
- Chart-pie: Cyan `#06b6d4`
- Server: Blue `#3b82f6`
- Plug: Cyan `#06b6d4`
- Shield: Purple `#a855f7`
- Chart-bar: Green `#10b981`
- Robot: Yellow `#f59e0b`

## Typography

### Fonts
- **Primary Font**: Inter (Google Fonts)
  - Weights: 300 (Light), 400 (Regular), 500 (Medium), 600 (Semi-bold), 700 (Bold)
- **Monospace**: Default system monospace (for API endpoints)

### Font Sizes
- **H1 (Title)**: 2.25rem (36px) - `text-4xl`
- **H2 (Section)**: 1.5rem (24px) - `text-2xl`
- **H3 (Card Title)**: 0.875rem (14px) - `text-sm`
- **Body**: 1rem (16px) - Base
- **Small**: 0.75rem (12px) - `text-xs`
- **Metric Numbers**: 1.875rem (30px) - `text-3xl`

## Component Details

### Status Indicator
```
┌─────────────────────┐
│ 🟢 OPERATIONAL      │  ← Pulsing green dot + text
└─────────────────────┘

States:
- 🟢 OPERATIONAL (Green) - System healthy
- 🟡 DEGRADED (Yellow) - Partial functionality
- 🔴 ERROR (Red) - System errors
```

### Metric Cards
```
┌──────────────────────────┐
│ Icon  Title          ↗   │  ← Hover: Lifts up 2px
│                          │
│ $1,000,000.00           │  ← Large number
│                          │
│ Small description       │  ← Gray subtitle
└──────────────────────────┘

Hover Effect:
- Transforms up 2px
- Blue shadow glow appears
- Border changes to blue
```

### Quick Action Buttons
```
┌─────────────────────────┐
│  📖 API Documentation   │  ← Gradient background
└─────────────────────────┘

Hover Effect:
- Scales to 105%
- Darker gradient
- Stronger shadow
```

### API Endpoint Links
```
GET /api/trading/portfolio   ← Clickable, hover indents

Hover Effect:
- Background: Blue translucent
- Text: Brighter white
- Padding-left increases
```

### Feature Cards
```
┌──────────────────────────┐
│ 🛡️ Risk Management      │
│                          │
│ Real-time position       │
│ sizing and risk          │
│ monitoring               │
└──────────────────────────┘

Style:
- Dark gray background
- Colored icon
- Centered text
```

## Responsive Breakpoints

### Desktop (md: 768px+)
- 4 columns for quick actions
- 4 columns for metric cards
- 2 columns for API endpoint panels
- 3 columns for feature cards

### Tablet (640px - 767px)
- 2 columns for quick actions
- 2 columns for metric cards
- 1 column for API endpoint panels
- 2 columns for feature cards

### Mobile (< 640px)
- 1 column for all sections
- Stack all cards vertically
- Full-width buttons
- Compressed padding

## Interactive States

### Loading State
```
Initial Capital: Loading...
```
- Gray text
- Shows while API is fetching

### Success State
```
Initial Capital: $1,000,000.00
```
- White text
- Data loaded successfully

### Error State
```
Initial Capital: Error
System Status: ERROR (Red)
```
- Red text for status
- Error message in console

### Dynamic Return Color
```
Total Return: +5.23% (Green)
Total Return: -2.45% (Red)
```
- Positive: Green `#10b981`
- Negative: Red `#ef4444`

## Animation Details

### Pulse Animation (Status Indicator)
```css
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}
Duration: 2s
Iteration: Infinite
```

### Card Hover Animation
```css
transition: all 0.3s ease
transform: translateY(-2px)
box-shadow: 0 10px 40px rgba(59, 130, 246, 0.2)
```

### Button Hover Animation
```css
transition: all 0.3s ease
transform: scale(1.05)
box-shadow: 0 10px 25px rgba(59, 130, 246, 0.4)
```

## Auto-refresh Behavior

### Timestamp Update
- **Frequency**: Every 1 second
- **Format**: `zh-TW` locale (e.g., "2025/10/25 上午11:30:45")

### Metrics Update
- **Frequency**: Every 10 seconds
- **APIs Called**:
  1. `/api/trading/portfolio` - For capital, value, positions
  2. `/api/trading/performance` - For total return
  3. `/health` - For system status

### Manual Refresh
- **Trigger**: Clicking "Refresh Metrics" button
- **Effect**: Immediately fetches all metrics

## Browser Compatibility

### Fully Supported
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

### Mobile Support
- iOS Safari 14+
- Chrome Mobile 90+
- Samsung Internet 14+

### Required Features
- CSS Grid Layout
- CSS Flexbox
- CSS Custom Properties (Variables)
- CSS Gradient
- CSS Backdrop Filter (for glass effect)
- ES6+ JavaScript (async/await, fetch API)

## Accessibility Features

### Keyboard Navigation
- All buttons and links are keyboard accessible
- Tab order follows logical flow
- Focus states visible

### Screen Readers
- Semantic HTML5 elements
- Icon + text labels
- ARIA-friendly structure

### Color Contrast
- Meets WCAG AA standards
- Text on dark backgrounds: High contrast
- Interactive elements: Clear visual distinction

## Performance Metrics

### Page Load
- **HTML Size**: ~15KB
- **External Resources**: 3 (Tailwind, Font Awesome, Google Fonts)
- **JavaScript**: Inline, minimal (~2KB)
- **First Contentful Paint**: < 1s (on good connection)

### Runtime Performance
- **API Calls**: Max 3 every 10 seconds
- **DOM Updates**: Minimal (only text content)
- **Memory Usage**: Low (no heavy libraries)

## Example Screenshots Description

### Desktop View (1920x1080)
```
Wide layout, 4-column grid for cards, spacious padding,
large font sizes, all content visible without scrolling.
```

### Tablet View (768x1024)
```
2-column layout for cards, slightly compressed padding,
API panels stacked vertically, scrolling required.
```

### Mobile View (375x667)
```
Single column layout, full-width cards, compact spacing,
touch-friendly button sizes, vertical scrolling.
```

## Developer Notes

### To Customize:
1. **Colors**: Modify CSS variables in `<style>` section
2. **API Endpoints**: Update links in "API Endpoints" section
3. **Metrics**: Modify `fetchSystemMetrics()` function
4. **Refresh Rate**: Change `setInterval` timing (line 332)

### To Extend:
1. Add new metric cards by copying existing card structure
2. Add new quick action buttons in the grid
3. Add charts using Chart.js (already included CDN in old version)
4. Add WebSocket connections for real-time updates

---

**Document Created:** 2025-10-25
**Dashboard Version:** 1.0.0
**Status:** Production Ready
