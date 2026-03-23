# BreakoutScan Design System

**Version:** 1.0
**Last Updated:** March 2026
**Platform:** BreakoutScan — India's Real-Time NSE/BSE Breakout Screener
**Author:** Adarsha Chatterjee

---

## Table of Contents

1. [Brand Overview](#1-brand-overview)
2. [Design Principles](#2-design-principles)
3. [Color System](#3-color-system)
4. [Typography](#4-typography)
5. [Spacing & Layout](#5-spacing--layout)
6. [Border Radius](#6-border-radius)
7. [Shadows & Elevation](#7-shadows--elevation)
8. [Glassmorphism](#8-glassmorphism)
9. [Components](#9-components)
10. [Animations & Motion](#10-animations--motion)
11. [Icons](#11-icons)
12. [Responsive Design](#12-responsive-design)
13. [Accessibility](#13-accessibility)
14. [Dark / Light Theme](#14-dark--light-theme)
15. [CSS Custom Properties Reference](#15-css-custom-properties-reference)

---

## 1. Brand Overview

**Product Name:** BreakoutScan (Codex Screener)
**Tagline:** India's Real-Time NSE/BSE Breakout Screener
**Domain:** Financial Technology / Stock Market Analysis
**Target Users:** Indian retail traders, swing traders, technical analysts

**Brand Personality:**
- Professional yet approachable
- Data-dense but not cluttered
- Real-time and dynamic
- Trustworthy with financial data

**Brand Colors:**
- Primary Accent: `#7C5CFC` (Electric Purple)
- Secondary Accent: `#00D4FF` (Cyan Blue)
- Bullish: `#00C796` (Emerald Green)
- Bearish: `#FF5A8A` (Coral Red)

---

## 2. Design Principles

### 2.1 Data Density Over Decoration
Every pixel serves a purpose. Financial interfaces demand high information density. Prioritize data legibility over visual flair.

### 2.2 Glassmorphism with Purpose
Use frosted glass effects to create depth hierarchy — not for decoration. Glass separates content layers (sidebar, cards, modals) from the ambient background.

### 2.3 Motion as Feedback
Animations exist to confirm user actions (flash on price change, slide-up on load). Never animate purely for aesthetics. All animations respect `prefers-reduced-motion`.

### 2.4 Mobile-First, Touch-Ready
All interactive elements meet 44px minimum touch targets. iOS safe areas are respected. Momentum scrolling is enabled everywhere.

### 2.5 Theme Adaptability
Every color is a CSS custom property. The entire UI switches between dark and light themes via a single `data-theme` attribute on `<html>`.

---

## 3. Color System

All colors are defined as CSS custom properties on `:root` and toggled via `[data-theme="dark"]` / `[data-theme="light"]`.

### 3.1 Background Colors

| Token | Dark Mode | Light Mode | Usage |
|-------|-----------|------------|-------|
| `--bg-page` | `#0A0E1A` | `#F0F2F8` | Page background |
| `--bg-sidebar` | `rgba(16, 22, 36, 0.85)` | `rgba(255, 255, 255, 0.7)` | Sidebar panel |
| `--bg-card` | `rgba(22, 29, 45, 0.75)` | `rgba(255, 255, 255, 0.6)` | Card surfaces |
| `--bg-elevated` | `rgba(28, 35, 51, 0.8)` | `rgba(255, 255, 255, 0.8)` | Elevated surfaces (topbar, hover states) |

### 3.2 Border Colors

| Token | Dark Mode | Light Mode | Usage |
|-------|-----------|------------|-------|
| `--border` | `rgba(35, 45, 64, 0.6)` | `rgba(200, 205, 220, 0.5)` | Standard borders |
| `--border-subtle` | `#1A2235` | `rgba(220, 225, 240, 0.4)` | Subtle dividers |

### 3.3 Accent Colors

| Token | Dark Mode | Light Mode | Usage |
|-------|-----------|------------|-------|
| `--accent` | `#7C5CFC` | `#7C5CFC` | Primary accent (buttons, links, active states) |
| `--accent-hover` | `#9B7FFF` | `#6A48E8` | Accent hover state |
| `--accent-glow` | `rgba(124, 92, 252, 0.2)` | `rgba(124, 92, 252, 0.15)` | Glow effects around accent elements |

### 3.4 Semantic Colors

| Token | Dark Mode | Light Mode | Usage |
|-------|-----------|------------|-------|
| `--bullish` | `#00C796` | `#00A878` | Positive values, price up, buy signals |
| `--bearish` | `#FF5A8A` | `#E5395F` | Negative values, price down, sell signals |
| `--warning` | `#FF8800` | `#E67E00` | Warnings, caution states |
| `--info` | `#00D4FF` | `#0097CC` | Informational, neutral highlights |

### 3.5 Text Colors

| Token | Dark Mode | Light Mode | Usage |
|-------|-----------|------------|-------|
| `--text-primary` | `#E8ECF4` | `#1A1F2E` | Primary body text, headings |
| `--text-secondary` | `#8B95A8` | `#666A7A` | Secondary text, labels |
| `--text-muted` | `#5A6478` | `#9CA3B0` | Muted text, placeholders, disabled |

### 3.6 Chart Colors

| Token | Dark Mode | Light Mode | Usage |
|-------|-----------|------------|-------|
| `--chart-grid` | `#1A2235` | `#E0E4EC` | Chart grid lines |
| `--chart-cross` | `#7C5CFC` | `#7C5CFC` | Crosshair on charts |

### 3.7 Glass Effect Colors

| Token | Dark Mode | Light Mode | Usage |
|-------|-----------|------------|-------|
| `--glass-bg` | `rgba(16, 22, 36, 0.6)` | `rgba(255, 255, 255, 0.5)` | Glass panel background |
| `--glass-border` | `rgba(124, 92, 252, 0.1)` | `rgba(200, 205, 220, 0.4)` | Glass panel border |
| `--glass-shadow` | `0 8px 32px rgba(0, 0, 0, 0.4)` | `0 8px 32px rgba(100, 100, 140, 0.12)` | Glass panel shadow |

### 3.8 Signal Badge Colors

Used in the screener for technical signal indicators:

| Signal | Background | Text | Border |
|--------|-----------|------|--------|
| BREAKOUT | `purple-500/20` | `purple-400` | `purple-500/30` |
| RSI | `cyan-500/20` | `cyan-400` | `cyan-500/30` |
| EMA | `orange-500/20` | `orange-400` | `orange-500/30` |
| MACD | `yellow-500/20` | `yellow-400` | `yellow-500/30` |
| VOLUME | `emerald-500/20` | `emerald-400` | `emerald-500/30` |
| PATTERN | `blue-500/20` | `blue-400` | `blue-500/30` |

---

## 4. Typography

### 4.1 Font Families

| Token | Font | Usage |
|-------|------|-------|
| `--font-inter` | **Inter** (Google Fonts) | All UI text — headings, body, labels, buttons |
| `--font-jetbrains-mono` | **JetBrains Mono** (Google Fonts) | Numeric data, prices, percentages, code |

**Tailwind Config:**
```css
font-sans: var(--font-inter)
font-mono: var(--font-jetbrains-mono)
```

### 4.2 Type Scale

| Element | Size | Weight | Class |
|---------|------|--------|-------|
| Page Title (H1) | 24px / `text-2xl` | 700 `font-bold` | — |
| Section Heading (H2) | 18–20px / `text-lg sm:text-xl` | 600 `font-semibold` | `SectionHeading` |
| Card Title (H3) | 16px / `text-base` | 600 `font-semibold` | — |
| Body Text | 14px / `text-sm` | 400 `font-normal` | — |
| Table Header | 11–12px / `text-[11px] sm:text-xs` | 500 `font-medium` | `uppercase tracking-wider` |
| Label | 12px / `text-xs` | 500 `font-medium` | `uppercase tracking-wider` |
| Caption / Muted | 10–12px / `text-[10px]` or `text-xs` | 400 | `text-text-muted` |

### 4.3 Numeric Display

All financial numbers use:
- `font-mono` (JetBrains Mono)
- `tabular-nums` (fixed-width digits for alignment)
- Class: `font-mono tabular-nums`

---

## 5. Spacing & Layout

### 5.1 Base Unit
The spacing system is based on a **4px grid** using Tailwind's default scale.

| Token | Value | Usage |
|-------|-------|-------|
| `gap-1` | 4px | Tight inline spacing |
| `gap-1.5` | 6px | Icon-to-text gap |
| `gap-2` | 8px | Label-to-input gap |
| `gap-3` | 12px | Card internal sections |
| `p-4` / `p-5` | 16px / 20px | Card padding (mobile / desktop) |
| `p-5` / `p-6` | 20px / 24px | Modal padding (mobile / desktop) |
| `gap-4` | 16px | Grid gaps between cards |

### 5.2 Page Layout

```
┌────────────────────────────────────────────────┐
│  Index Ticker Bar (full width, scrolling)       │
├──────────┬─────────────────────────────────────┤
│          │  Topbar (glass, blur 16px)           │
│ Sidebar  ├─────────────────────────────────────┤
│ (glass,  │                                     │
│  blur    │  Main Content Area                  │
│  20px)   │  (page-transition animated)         │
│          │                                     │
│  Hidden  │  ┌─────────┐  ┌─────────┐          │
│  on      │  │ Card    │  │ Card    │          │
│  mobile  │  │ (glass) │  │ (glass) │          │
│          │  └─────────┘  └─────────┘          │
├──────────┴─────────────────────────────────────┤
│  Mobile Bottom Nav (sm:hidden, safe-area)       │
└────────────────────────────────────────────────┘
```

### 5.3 Responsive Breakpoints

Using Tailwind defaults:
| Breakpoint | Width | Usage |
|------------|-------|-------|
| Default | 0px | Mobile-first base styles |
| `sm` | 640px | Tablet / small desktop |
| `md` | 768px | Desktop sidebar visible |
| `lg` | 1024px | Full desktop layout |

---

## 6. Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `rounded-panel` | `12px` | Cards, panels, containers |
| `rounded-xl` | `12px` | Buttons, inputs, modals |
| `rounded-2xl` | `16px` | Modal on desktop |
| `rounded-t-2xl` | `16px` top | Modal on mobile (bottom sheet) |
| `rounded-full` | `9999px` | Badges, pills, dots |
| `rounded-lg` | `8px` | Skeleton loaders, small elements |

---

## 7. Shadows & Elevation

| Token | Value | Usage |
|-------|-------|-------|
| `shadow-card` | `0 4px 24px rgba(0, 0, 0, 0.5)` | Default card shadow |
| `shadow-accent` | `0 4px 20px rgba(124, 92, 252, 0.25)` | Primary button shadow |
| `shadow-glow` | `0 0 20px rgba(124, 92, 252, 0.15)` | Hover glow on cards |
| `--glass-shadow` | `0 8px 32px rgba(0, 0, 0, 0.4)` | Glass panel shadow (dark) |
| `shadow-2xl` | Tailwind default | Modal shadow |

**Elevation Hierarchy (lowest to highest):**
1. Page background (`--bg-page`)
2. Card surface (`--bg-card` + `shadow-card`)
3. Sidebar / Topbar (`--bg-sidebar` / `--bg-elevated`)
4. Modal overlay (`bg-black/70` + `backdrop-blur-sm`)
5. Modal content (`--bg-card` + `shadow-2xl`)

---

## 8. Glassmorphism

The core visual identity uses layered frosted glass panels.

### 8.1 Glass Utility Classes

| Class | Blur | Background | Border | Usage |
|-------|------|-----------|--------|-------|
| `.glass` | `12px` | `var(--glass-bg)` | `var(--glass-border)` | Generic glass panels |
| `.glass-card` | `16px` | `var(--bg-card)` | `var(--border)` | Content cards |
| `.glass-sidebar` | `20px` | `var(--bg-sidebar)` | Right border | Navigation sidebar |
| `.glass-topbar` | `16px` | `var(--bg-elevated)` | Bottom border | Top navigation bar |

### 8.2 Glass Card Hover Effect

```css
.glass-card:hover {
  box-shadow: 0 0 24px var(--accent-glow), var(--glass-shadow);
  border-color: rgba(124, 92, 252, 0.2);
  transform: translateY(-2px);
}
```

### 8.3 Ambient Glow

Cards with `.ambient-glow` get a blurred purple-cyan gradient behind them on hover:
```css
background: linear-gradient(135deg, rgba(124, 92, 252, 0.15), rgba(0, 212, 255, 0.08));
filter: blur(12px);
```

### 8.4 Dark Mode Background Gradients

```css
/* Page background — dark */
background:
  radial-gradient(ellipse at 20% 0%, rgba(124, 92, 252, 0.08), transparent 50%),
  radial-gradient(ellipse at 80% 100%, rgba(0, 212, 255, 0.04), transparent 50%),
  linear-gradient(180deg, #0c1020 0%, #0a0e1a 40%, #080c16 100%);

/* Page background — light */
background:
  radial-gradient(ellipse at 0% 0%, rgba(124, 92, 252, 0.12), transparent 50%),
  radial-gradient(ellipse at 100% 0%, rgba(236, 72, 153, 0.08), transparent 50%),
  radial-gradient(ellipse at 50% 100%, rgba(59, 130, 246, 0.06), transparent 50%),
  linear-gradient(180deg, #e8eaf4 0%, #f0f2f8 40%, #f5f6fc 100%);
```

---

## 9. Components

### 9.1 Button

**Variants:**

| Variant | Style | Usage |
|---------|-------|-------|
| `primary` | Purple gradient (`#7C5CFC` → `#5B3FD4`), white text, accent shadow | Primary actions (Apply, Save, Buy) |
| `secondary` | Transparent, accent border, accent text | Secondary actions (Cancel, Filter) |
| `ghost` | No background, secondary text, elevated bg on hover | Tertiary actions (Close, Toggle) |

**Sizes:**

| Size | Height | Padding | Font |
|------|--------|---------|------|
| `sm` | 36px (`h-9`) | `px-3` | 12px (`text-xs`) |
| `md` | 40–44px (`h-10 sm:h-11`) | `px-4 sm:px-5` | 14px (`text-sm`) |
| `lg` | 48px (`h-12`) | `px-6` | 16px (`text-base`) |

**Behavior:**
- `press-scale` on `:active` — scales to `0.97`
- Haptic feedback on tap (mobile)
- `disabled:opacity-50 disabled:pointer-events-none`
- Transition: `all 200ms`

### 9.2 Card

```
┌─────────────────────────────┐
│  border: 1px solid --border │
│  bg: --bg-card              │
│  border-radius: 12px       │
│  padding: 16px (sm: 20px)  │
│  shadow: shadow-card        │
│                             │
│  Hover: translateY(-2px)    │
│  Hover: border → accent/20  │
│  Hover: shadow → glow       │
│  Hover: ambient-glow        │
└─────────────────────────────┘
```

### 9.3 Badge

Pill-shaped status indicators.

| Variant | Background | Text | Border |
|---------|-----------|------|--------|
| `bullish` | `bullish/12%` | `--bullish` | `bullish/25%` |
| `bearish` | `bearish/12%` | `--bearish` | `bearish/25%` |
| `neutral` | `text-secondary/12%` | `--text-secondary` | `text-secondary/25%` |
| `accent` | `accent/12%` | `--accent-hover` | `accent/25%` |
| `warning` | `warning/12%` | `--warning` | `warning/25%` |

**Style:** `rounded-full`, `px-2.5 py-0.5`, `text-xs font-semibold`, `border`

### 9.4 Input

- Height: `44px` (`h-11`)
- Border radius: `12px` (`rounded-xl`)
- Background: `--bg-page`
- Border: `--border`
- Focus: `border-accent` + `ring-2 ring-accent/15`
- Error: `border-bearish` + `ring-bearish/20`
- Label: `text-xs font-medium uppercase tracking-wider text-text-secondary`
- Placeholder: `text-text-muted`

### 9.5 Modal

- **Mobile:** Bottom sheet (`rounded-t-2xl`, slides up from bottom, drag handle bar)
- **Desktop:** Centered dialog (`rounded-2xl`, scales in)
- Backdrop: `bg-black/70 backdrop-blur-sm`
- Content: `--bg-card`, `border-border`, `shadow-2xl`
- Max height: `80vh` (mobile), `85vh` (desktop)
- Close: Escape key, backdrop click, X button
- Body scroll locked when open

### 9.6 Data Table

- Header: `text-[11px] sm:text-xs`, `uppercase tracking-wider`, `text-text-secondary`
- Sort indicators: `ArrowUpDown` / `ArrowUp` / `ArrowDown` (Lucide icons, 12px)
- Row animation: `fade-in` + `translateY(12px)` staggered at `50ms` per row
- Alternating rows: even = transparent, odd = `bg-page/40`
- Hover (clickable): `bg-elevated`
- Cell padding: `px-3 sm:px-4 py-3`
- Horizontal scroll with momentum (`scroll-touch`)

### 9.7 Section Heading

```
┌─────────────────────────────────────┐
│  Title (lg/xl, semibold, primary)   │
│  Subtitle (sm, secondary)    [Action] │
└─────────────────────────────────────┘
```

### 9.8 Skeleton Loader

- Animated shimmer gradient: `card → elevated → card` sliding left
- Duration: `1.5s ease-in-out infinite`
- Variants: `Skeleton` (custom size), `SkeletonCard`, `SkeletonTable`

### 9.9 Live Dot

Pulsing status indicator with ping animation.

| Color | CSS Class | Usage |
|-------|-----------|-------|
| `green` | `bg-bullish` | Market open, live data |
| `red` | `bg-bearish` | Market closed, errors |
| `yellow` | `bg-warning` | Pre-market, delayed data |

### 9.10 Price Cell

- Font: `font-mono tabular-nums`
- Flash animation on price change:
  - **Up:** Green background flash (`flash-bullish`) + green text
  - **Down:** Red background flash (`flash-bearish`) + red text
- Duration: `600ms ease-out`

### 9.11 Countdown Bar

Market session progress indicator:
- Track: `h-1.5`, `rounded-full`, `bg-border`
- Fill: gradient `accent → bullish`
- Labels: open time, status, close time (`text-[10px]`)

### 9.12 Signal Badge

Technical signal pills with color-coded backgrounds per signal type (BREAKOUT, RSI, EMA, MACD, VOLUME, PATTERN).

---

## 10. Animations & Motion

### 10.1 Keyframe Animations

| Animation | Duration | Easing | Description |
|-----------|----------|--------|-------------|
| `fade-in` | 300ms | `ease-out` | Opacity 0 → 1 |
| `slide-up` | 350ms | `cubic-bezier(0.4, 0, 0.2, 1)` | Opacity 0 + translateY(12px) → visible |
| `scale-in` | 200ms | `cubic-bezier(0.4, 0, 0.2, 1)` | Opacity 0 + scale(0.95) → visible |
| `shimmer` | 2s | `ease-in-out infinite` | Background position shift for loading |
| `glow-pulse` | — | `infinite` | Box-shadow pulse (accent glow) |
| `slide-in` | — | — | translateX(-12px) → 0 |
| `ticker-scroll` | — | — | translateX(0) → translateX(-50%) for ticker |
| `flash-bullish` | 600ms | `ease-out` | Green bg flash + scale(1.02) → transparent |
| `flash-bearish` | 600ms | `ease-out` | Red bg flash + scale(1.02) → transparent |
| `pulse-dot` | 1.5s | `ease-in-out infinite` | Opacity + scale pulse for live dots |

### 10.2 Page Transitions

Using the **View Transitions API** (`view-transition-name: page-content`):
- Exit: `fade-out-slide` (250ms) — opacity 1→0, translateY(0→-8px)
- Enter: `fade-in-slide` (300ms) — opacity 0→1, translateY(12px→0)
- Respects `prefers-reduced-motion` (set to `0ms` duration)

### 10.3 Interaction Animations

| Interaction | Effect |
|------------|--------|
| Button press | `scale(0.97)` via `.press-scale:active` |
| Card hover | `translateY(-2px)` + accent glow border |
| Modal enter | `opacity 0→1`, `translateY(60→0)`, `scale(0.98→1)` at 250ms |
| Modal exit | `opacity 1→0`, `translateY(0→40)`, `scale(1→0.98)` |
| Table row enter | `opacity 0→1`, `translateY(12→0)` staggered at 50ms |
| Theme change | `background 400ms ease`, `color 300ms ease` |

### 10.4 Timing Function

Custom easing: `ease-out-expo` = `cubic-bezier(0.16, 1, 0.3, 1)` — fast start, gentle stop.

---

## 11. Icons

**Library:** [Lucide React](https://lucide.dev/)

| Icon | Component | Usage |
|------|-----------|-------|
| Sort | `ArrowUpDown`, `ArrowUp`, `ArrowDown` | Table column sort |
| Close | `X` | Modal close button |
| Navigation | Various Lucide icons | Sidebar menu items |

**Default Size:** `h-5 w-5` (20px) for actions, `h-3 w-3` (12px) for inline indicators.

---

## 12. Responsive Design

### 12.1 Mobile Optimizations

- **Touch targets:** Min `44px × 44px` on mobile (`@media max-width: 639px`)
- **Safe areas:** `env(safe-area-inset-*)` for iPhone notch/home indicator
- **Momentum scroll:** `-webkit-overflow-scrolling: touch` + hidden scrollbars
- **Scroll fade hints:** Horizontal scroll areas get edge fade masks
- **Bottom sheet modals:** Full-width, rounded-top, with drag handle
- **Mobile nav:** Bottom tab bar (hidden on desktop)

### 12.2 Desktop Enhancements

- Sidebar visible (hidden on mobile)
- Larger padding on cards (`p-5` vs `p-4`)
- Larger button heights (`h-11` vs `h-10`)
- Centered modals with `rounded-2xl`

---

## 13. Accessibility

### 13.1 Color Contrast
- Primary text on dark bg: `#E8ECF4` on `#0A0E1A` = **13.8:1** (AAA)
- Secondary text on dark bg: `#8B95A8` on `#0A0E1A` = **6.2:1** (AA)
- Bullish green on dark bg: `#00C796` = **8.1:1** (AAA)
- Bearish red on dark bg: `#FF5A8A` = **5.3:1** (AA)

### 13.2 Motion
- All animations respect `prefers-reduced-motion: reduce`
- View transitions disabled when reduced motion preferred

### 13.3 Focus States
- Inputs show `ring-2 ring-accent/15` on focus
- Buttons and interactive elements use `outline` via browser defaults

### 13.4 Semantic HTML
- Modals use `aria-label` on close buttons
- Tables use proper `<thead>`, `<tbody>`, `<th>`, `<td>` structure
- Body scroll locked when modal is open

---

## 14. Dark / Light Theme

### 14.1 Implementation

Theme is controlled by a `data-theme` attribute on `<html>`:

```html
<html data-theme="dark"> <!-- or "light" -->
```

Toggled via `ThemeProvider` context component. The meta `theme-color` tag also updates for the browser chrome.

### 14.2 Theme-Specific Body Backgrounds

**Dark:** Deep navy with subtle purple/cyan radial gradients
**Light:** Soft lavender-white with purple/pink/blue radial gradients

### 14.3 Key Differences

| Element | Dark | Light |
|---------|------|-------|
| Page bg | Deep navy `#0A0E1A` | Soft lavender `#F0F2F8` |
| Cards | Dark translucent | White translucent |
| Accent hover | Lighter `#9B7FFF` | Darker `#6A48E8` |
| Bullish | Bright `#00C796` | Muted `#00A878` |
| Bearish | Bright `#FF5A8A` | Muted `#E5395F` |
| Shadows | Heavy, dark | Light, subtle |
| Glass border | Purple-tinted | Gray-tinted |
| Color scheme | `dark` | `light` |

---

## 15. CSS Custom Properties Reference

Complete token reference for implementation:

```css
:root, [data-theme="dark"] {
  /* Backgrounds */
  --bg-page: #0a0e1a;
  --bg-sidebar: rgba(16, 22, 36, 0.85);
  --bg-card: rgba(22, 29, 45, 0.75);
  --bg-elevated: rgba(28, 35, 51, 0.8);

  /* Borders */
  --border: rgba(35, 45, 64, 0.6);
  --border-subtle: #1a2235;

  /* Accent */
  --accent: #7c5cfc;
  --accent-hover: #9b7fff;
  --accent-glow: rgba(124, 92, 252, 0.2);

  /* Semantic */
  --bullish: #00c796;
  --bearish: #ff5a8a;
  --warning: #ff8800;
  --info: #00d4ff;

  /* Text */
  --text-primary: #e8ecf4;
  --text-secondary: #8b95a8;
  --text-muted: #5a6478;

  /* Chart */
  --chart-grid: #1a2235;
  --chart-cross: #7c5cfc;

  /* Glass */
  --glass-bg: rgba(16, 22, 36, 0.6);
  --glass-border: rgba(124, 92, 252, 0.1);
  --glass-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);

  color-scheme: dark;
}

[data-theme="light"] {
  --bg-page: #f0f2f8;
  --bg-sidebar: rgba(255, 255, 255, 0.7);
  --bg-card: rgba(255, 255, 255, 0.6);
  --bg-elevated: rgba(255, 255, 255, 0.8);
  --border: rgba(200, 205, 220, 0.5);
  --border-subtle: rgba(220, 225, 240, 0.4);
  --accent: #7c5cfc;
  --accent-hover: #6a48e8;
  --accent-glow: rgba(124, 92, 252, 0.15);
  --bullish: #00a878;
  --bearish: #e5395f;
  --warning: #e67e00;
  --info: #0097cc;
  --text-primary: #1a1f2e;
  --text-secondary: #666a7a;
  --text-muted: #9ca3b0;
  --chart-grid: #e0e4ec;
  --chart-cross: #7c5cfc;
  --glass-bg: rgba(255, 255, 255, 0.5);
  --glass-border: rgba(200, 205, 220, 0.4);
  --glass-shadow: 0 8px 32px rgba(100, 100, 140, 0.12);
  color-scheme: light;
}
```

### Tailwind Extended Tokens

```js
// tailwind.config.ts
colors: {
  page, sidebar, card, elevated, border, "border-subtle",
  accent: { DEFAULT, hover, glow },
  bullish, bearish, warning, info,
  "text-primary", "text-secondary", "text-muted"
}
boxShadow: { card, accent, glow }
borderRadius: { panel: "12px" }
fontFamily: { sans: ["var(--font-inter)"], mono: ["var(--font-jetbrains-mono)"] }
```

---

## Appendix: File Map

| File | Purpose |
|------|---------|
| `apps/web/src/app/globals.css` | All CSS custom properties, glass utilities, animations, scrollbar, theme backgrounds |
| `apps/web/tailwind.config.ts` | Tailwind token extensions (colors, shadows, fonts, animations) |
| `apps/web/src/components/ui/button.tsx` | Button component (3 variants, 3 sizes, haptic) |
| `apps/web/src/components/ui/card.tsx` | Card component (glass, hover, ambient glow) |
| `apps/web/src/components/ui/badge.tsx` | Badge component (5 semantic variants) |
| `apps/web/src/components/ui/input.tsx` | Input component (label, error, focus ring) |
| `apps/web/src/components/ui/modal.tsx` | Modal component (bottom sheet / centered, Framer Motion) |
| `apps/web/src/components/ui/skeleton.tsx` | Skeleton loaders (shimmer animation) |
| `apps/web/src/components/ui/data-table.tsx` | Data table (TanStack, sortable, animated rows) |
| `apps/web/src/components/ui/section-heading.tsx` | Section heading (title + subtitle + action) |
| `apps/web/src/components/ui/live-dot.tsx` | Live status dot (ping animation) |
| `apps/web/src/components/ui/price-cell.tsx` | Price cell (flash on change) |
| `apps/web/src/components/ui/countdown-bar.tsx` | Market session progress bar |
| `apps/web/src/components/shared/signal-badge.tsx` | Technical signal badges (6 types) |
| `apps/web/src/components/providers/theme-provider.tsx` | Theme toggle context provider |

---

*BreakoutScan Design System v1.0 — Built with Next.js, Tailwind CSS, Framer Motion, and Lucide Icons*
