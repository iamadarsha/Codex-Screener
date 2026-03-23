#!/usr/bin/env python3
"""
BreakoutScan Design System — Professional Brand Book PDF Generator
Author: Adarsha Chatterjee
Generates a 40-60 page design system document with rich visual styling.
"""

from fpdf import FPDF
import math
import os

# ── Brand Colors ──────────────────────────────────────────────────
DARK_BG = (10, 14, 26)
DARK_CARD = (22, 29, 45)
DARK_ELEVATED = (28, 35, 51)
WHITE = (255, 255, 255)
LIGHT_GRAY = (200, 205, 220)
MID_GRAY = (139, 149, 168)
MUTED = (90, 100, 120)
ACCENT = (124, 92, 252)
ACCENT_HOVER = (155, 127, 255)
CYAN = (0, 212, 255)
BULLISH = (0, 199, 150)
BEARISH = (255, 90, 138)
WARNING = (255, 136, 0)
INFO = (0, 212, 255)
SOFT_PURPLE = (94, 72, 192)
LIGHT_BG = (240, 242, 248)
SECTION_BORDER = (55, 65, 90)


class DesignSystemPDF(FPDF):

    def __init__(self):
        super().__init__("P", "mm", "A4")
        self.set_auto_page_break(auto=True, margin=20)

    def _draw_page_bg(self, dark=True):
        if dark:
            self.set_fill_color(*DARK_BG)
        else:
            self.set_fill_color(*LIGHT_BG)
        self.rect(0, 0, 210, 297, "F")

    def _draw_accent_bar(self, y, width=210):
        steps = 60
        bar_h = 2
        for i in range(steps):
            ratio = i / steps
            r = int(ACCENT[0] + (CYAN[0] - ACCENT[0]) * ratio)
            g = int(ACCENT[1] + (CYAN[1] - ACCENT[1]) * ratio)
            b = int(ACCENT[2] + (CYAN[2] - ACCENT[2]) * ratio)
            self.set_fill_color(r, g, b)
            x = (width / steps) * i
            self.rect(x, y, width / steps + 0.5, bar_h, "F")

    def _draw_gradient_rect(self, x, y, w, h, color1, color2, vertical=True):
        steps = 40
        if vertical:
            step_h = h / steps
            for i in range(steps):
                ratio = i / steps
                r = int(color1[0] + (color2[0] - color1[0]) * ratio)
                g = int(color1[1] + (color2[1] - color1[1]) * ratio)
                b = int(color1[2] + (color2[2] - color1[2]) * ratio)
                self.set_fill_color(r, g, b)
                self.rect(x, y + step_h * i, w, step_h + 0.3, "F")
        else:
            step_w = w / steps
            for i in range(steps):
                ratio = i / steps
                r = int(color1[0] + (color2[0] - color1[0]) * ratio)
                g = int(color1[1] + (color2[1] - color1[1]) * ratio)
                b = int(color1[2] + (color2[2] - color1[2]) * ratio)
                self.set_fill_color(r, g, b)
                self.rect(x + step_w * i, y, step_w + 0.3, h, "F")

    def _draw_color_swatch(self, x, y, size, color, label, hex_code, dark_bg=True):
        self.set_fill_color(*color)
        self.ellipse(x, y, size, size, "F")
        self.set_draw_color(*(SECTION_BORDER if dark_bg else LIGHT_GRAY))
        self.set_line_width(0.3)
        self.ellipse(x, y, size, size, "D")
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*(WHITE if dark_bg else DARK_BG))
        self.set_xy(x - 2, y + size + 2)
        self.cell(size + 4, 4, label, align="C")
        self.set_font("Courier", "", 7)
        self.set_text_color(*(MID_GRAY if dark_bg else MUTED))
        self.set_xy(x - 2, y + size + 6)
        self.cell(size + 4, 4, hex_code, align="C")

    def _section_title(self, number, title, y=None):
        if y is None:
            y = self.get_y()
        badge_x = 20
        badge_size = 12
        self.set_fill_color(*ACCENT)
        self.ellipse(badge_x, y, badge_size, badge_size, "F")
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*WHITE)
        self.set_xy(badge_x, y + 1.5)
        self.cell(badge_size, badge_size - 3, str(number), align="C")
        self.set_font("Helvetica", "B", 20)
        self.set_text_color(*WHITE)
        self.set_xy(badge_x + badge_size + 6, y)
        self.cell(0, badge_size, title)
        self._draw_gradient_rect(badge_x, y + badge_size + 3, 170, 1, ACCENT, CYAN, vertical=False)
        self.set_y(y + badge_size + 10)

    def _subsection_title(self, title):
        y = self.get_y()
        self.set_fill_color(*ACCENT)
        self.rect(20, y + 2, 3, 8, "F")
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*WHITE)
        self.set_xy(27, y)
        self.cell(0, 12, title)
        self.set_y(y + 14)

    def _body_text(self, text, indent=20, width=170):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*LIGHT_GRAY)
        self.set_x(indent)
        self.multi_cell(width, 5.5, text)
        self.ln(2)

    def _bullet_point(self, text, indent=24, bullet_color=ACCENT):
        y = self.get_y()
        self.set_fill_color(*bullet_color)
        self.ellipse(indent, y + 1.5, 2.5, 2.5, "F")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*LIGHT_GRAY)
        self.set_xy(indent + 6, y)
        self.multi_cell(160, 5.5, text)
        self.ln(1)

    def _key_value(self, key, value, indent=24):
        y = self.get_y()
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*ACCENT_HOVER)
        self.set_xy(indent, y)
        self.cell(40, 6, key + ":")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*LIGHT_GRAY)
        self.set_xy(indent + 42, y)
        self.multi_cell(124, 6, value)
        self.ln(1)

    def _table(self, headers, rows, col_widths=None, indent=20):
        if col_widths is None:
            total = 170
            col_widths = [total / len(headers)] * len(headers)
        y = self.get_y()
        x = indent
        row_h = 8
        self.set_fill_color(*ACCENT)
        self.rect(x, y, sum(col_widths), row_h, "F")
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*WHITE)
        cx = x
        for i, h in enumerate(headers):
            self.set_xy(cx + 2, y + 1)
            self.cell(col_widths[i] - 4, row_h - 2, h)
            cx += col_widths[i]
        y += row_h
        for ri, row in enumerate(rows):
            if y > 270:
                self.add_page()
                self._draw_page_bg()
                y = 25
                self.set_fill_color(*ACCENT)
                self.rect(x, y, sum(col_widths), row_h, "F")
                self.set_font("Helvetica", "B", 8)
                self.set_text_color(*WHITE)
                cx = x
                for i, h in enumerate(headers):
                    self.set_xy(cx + 2, y + 1)
                    self.cell(col_widths[i] - 4, row_h - 2, h)
                    cx += col_widths[i]
                y += row_h
            if ri % 2 == 0:
                self.set_fill_color(18, 24, 38)
            else:
                self.set_fill_color(14, 19, 32)
            self.rect(x, y, sum(col_widths), row_h, "F")
            self.set_draw_color(*SECTION_BORDER)
            self.set_line_width(0.1)
            self.rect(x, y, sum(col_widths), row_h, "D")
            self.set_font("Courier", "", 8)
            self.set_text_color(*LIGHT_GRAY)
            cx = x
            for i, cell_val in enumerate(row):
                self.set_xy(cx + 2, y + 1)
                max_chars = int(col_widths[i] / 2)
                self.cell(col_widths[i] - 4, row_h - 2, str(cell_val)[:max_chars])
                cx += col_widths[i]
            y += row_h
        self.set_y(y + 4)

    def _code_block(self, code, indent=20, width=170):
        y = self.get_y()
        lines = code.strip().split("\n")
        block_h = len(lines) * 5 + 8
        if y + block_h > 275:
            self.add_page()
            self._draw_page_bg()
            y = 25
        self.set_fill_color(16, 20, 32)
        self.set_draw_color(*SECTION_BORDER)
        self.set_line_width(0.3)
        self.rect(indent, y, width, block_h, "DF")
        self.set_fill_color(*ACCENT)
        self.rect(indent, y, 2, block_h, "F")
        self.set_font("Courier", "", 7.5)
        self.set_text_color(180, 190, 210)
        ty = y + 4
        for line in lines:
            self.set_xy(indent + 6, ty)
            self.cell(width - 10, 5, line[:90])
            ty += 5
        self.set_y(y + block_h + 4)

    def _page_number_footer(self):
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*MUTED)
        self.set_xy(0, 287)
        self.cell(105, 5, "BreakoutScan Design System v1.0", align="R")
        self.cell(105, 5, f"  |  Page {self.page_no()}", align="L")

    def _check_space(self, needed=30):
        if self.get_y() > 297 - needed:
            self.add_page()
            self._draw_page_bg()
            self._page_number_footer()
            self.set_y(25)

    # ══════════════════════════════════════════════════════════════
    # PAGE BUILDERS
    # ══════════════════════════════════════════════════════════════

    def build_cover(self):
        self.add_page()
        self._draw_page_bg()
        self._draw_accent_bar(0)

        # Decorative bg
        self.set_fill_color(15, 18, 30)
        self.rect(0, 85, 210, 130, "F")

        # Logo mark
        self.set_fill_color(*ACCENT)
        self.ellipse(85, 55, 40, 40, "F")
        self.set_font("Helvetica", "B", 30)
        self.set_text_color(*WHITE)
        self.set_xy(85, 60)
        self.cell(40, 30, "BS", align="C")

        self.set_font("Helvetica", "B", 36)
        self.set_text_color(*WHITE)
        self.set_xy(0, 105)
        self.cell(210, 18, "BreakoutScan", align="C")

        self.set_font("Helvetica", "", 16)
        self.set_text_color(*ACCENT_HOVER)
        self.set_xy(0, 125)
        self.cell(210, 10, "Design System & Brand Guidelines", align="C")

        self.set_font("Helvetica", "", 11)
        self.set_text_color(*MID_GRAY)
        self.set_xy(0, 140)
        self.cell(210, 8, "Version 1.0  |  March 2026", align="C")

        self._draw_accent_bar(160)

        self.set_font("Helvetica", "I", 12)
        self.set_text_color(*CYAN)
        self.set_xy(0, 170)
        self.cell(210, 8, "India's Real-Time NSE/BSE Breakout Screener", align="C")

        self.set_font("Helvetica", "", 10)
        self.set_text_color(*MID_GRAY)
        self.set_xy(0, 185)
        self.cell(210, 6, "Created by Adarsha Chatterjee", align="C")
        self.set_xy(0, 192)
        self.cell(210, 6, "adarsha.chatterjee@gmail.com", align="C")

        self._draw_gradient_rect(20, 270, 170, 2, ACCENT, CYAN, vertical=False)

        self.set_font("Helvetica", "", 7)
        self.set_text_color(*MUTED)
        self.set_xy(0, 280)
        self.cell(210, 5, "CONFIDENTIAL  |  For internal and partner use only", align="C")

    def build_toc(self):
        self.add_page()
        self._draw_page_bg()
        self._page_number_footer()

        self.set_font("Helvetica", "B", 28)
        self.set_text_color(*WHITE)
        self.set_xy(20, 20)
        self.cell(170, 14, "Table of Contents")
        self._draw_gradient_rect(20, 36, 170, 1.5, ACCENT, CYAN, vertical=False)

        sections = [
            ("01", "Brand Overview", "Brand mission, vision, values, personality, story"),
            ("02", "Logo System", "Primary logo, variations, clear space, usage rules"),
            ("03", "Color System", "Primary, secondary, semantic, chart, glass colors"),
            ("04", "Typography System", "Type scale, font families, numeric display"),
            ("05", "Spacing System", "4px grid, component spacing, layout padding"),
            ("06", "Grid System", "Desktop, tablet, mobile grids and breakpoints"),
            ("07", "UI Components", "Buttons, cards, inputs, modals, tables, badges"),
            ("08", "Iconography", "Icon library, sizes, usage guidelines"),
            ("09", "Glassmorphism", "Glass panels, blur effects, ambient glow"),
            ("10", "Shadows & Elevation", "Shadow system, elevation hierarchy"),
            ("11", "Motion Guidelines", "Animations, transitions, easing curves"),
            ("12", "Dark / Light Theme", "Theme tokens, switching, key differences"),
            ("13", "Accessibility", "Color contrast, focus states, motion prefs"),
            ("14", "Responsive Design", "Mobile-first, touch targets, safe areas"),
            ("15", "Design Tokens", "CSS custom properties, Tailwind config"),
            ("16", "Component File Map", "Source file references and architecture"),
        ]

        y = 48
        for num, title, desc in sections:
            self.set_fill_color(*ACCENT)
            self.rect(20, y, 14, 14, "F")
            self.set_font("Helvetica", "B", 10)
            self.set_text_color(*WHITE)
            self.set_xy(20, y + 2)
            self.cell(14, 10, num, align="C")
            self.set_font("Helvetica", "B", 12)
            self.set_text_color(*WHITE)
            self.set_xy(40, y)
            self.cell(130, 7, title)
            self.set_font("Helvetica", "", 8.5)
            self.set_text_color(*MID_GRAY)
            self.set_xy(40, y + 7)
            self.cell(130, 5, desc)
            self.set_draw_color(*SECTION_BORDER)
            self.set_line_width(0.2)
            self.dashed_line(20, y + 16, 190, y + 16, 1, 2)
            y += 20

    def build_brand_overview(self):
        self.add_page()
        self._draw_page_bg()
        self._page_number_footer()
        self._section_title(1, "Brand Overview")

        self._subsection_title("Brand Mission")
        self._body_text(
            "To democratize real-time stock market intelligence for Indian retail traders by providing "
            "institutional-grade breakout detection, AI-powered stock analysis, and professional-grade "
            "technical screening tools -- all accessible from any device, at zero cost."
        )

        self._subsection_title("Brand Vision")
        self._body_text(
            "To become India's most trusted real-time stock screener platform, empowering every retail "
            "trader with the same data advantages that institutional investors have -- powered by AI, "
            "designed with clarity, and built for speed."
        )

        self._subsection_title("Brand Values")
        values = [
            ("Transparency", "Every data point is real, every signal is explainable, every score has methodology behind it."),
            ("Speed", "Real-time data, instant screener results, sub-second UI responses. Time is money in trading."),
            ("Accessibility", "Free tier with full functionality. Mobile-first design. Works on any connection."),
            ("Intelligence", "3-layer AI analysis with graceful fallback. Smart defaults. Adaptive interfaces."),
            ("Trust", "No hidden fees, no pump-and-dump signals, no misleading data. SEBI-conscious design."),
        ]
        for title, desc in values:
            self._check_space(20)
            y = self.get_y()
            self.set_fill_color(*ACCENT)
            self.rect(24, y + 1, 2.5, 2.5, "F")
            self.set_font("Helvetica", "B", 10)
            self.set_text_color(*ACCENT_HOVER)
            self.set_xy(30, y)
            self.cell(35, 6, title)
            self.set_font("Helvetica", "", 9.5)
            self.set_text_color(*LIGHT_GRAY)
            self.set_xy(65, y)
            self.multi_cell(125, 5.5, desc)
            self.ln(2)

        self._check_space(60)
        self._subsection_title("Brand Personality")
        personality = [
            "Professional yet approachable -- serious about data, friendly in design",
            "Data-dense but not cluttered -- high information density with clear hierarchy",
            "Real-time and dynamic -- live data, animated transitions, responsive feedback",
            "Trustworthy with financial data -- accurate, transparent, SEBI-compliant",
            "Modern and premium -- glass effects, dark theme, polished interactions",
        ]
        for p in personality:
            self._check_space(12)
            self._bullet_point(p)

        self._check_space(50)
        self._subsection_title("Brand Positioning")
        self._body_text(
            "BreakoutScan positions itself at the intersection of professional trading tools and consumer "
            "accessibility. Unlike Bloomberg Terminal (too expensive, too complex) or basic stock apps "
            "(too simple, no real-time data), BreakoutScan delivers institutional-grade breakout detection "
            "with a consumer-friendly interface.\n\n"
            "Target: Indian retail traders, swing traders, and technical analysts who need real-time "
            "NSE/BSE data with AI-powered insights -- on mobile or desktop."
        )

        self._check_space(50)
        self._subsection_title("Brand Story")
        self._body_text(
            "BreakoutScan was born from a simple frustration: retail traders in India deserved better tools. "
            "While institutional investors had access to real-time screeners, AI analysis, and breakout "
            "detection, retail traders were stuck with delayed data and basic charts.\n\n"
            "Built from the ground up with a 3-layer AI engine, 13 prebuilt screening strategies, and a "
            "glassmorphic dark-mode interface, BreakoutScan brings professional-grade market intelligence "
            "to every trader's phone and desktop."
        )

        self._check_space(40)
        self._subsection_title("Tone of Voice")
        tone_items = [
            ("Confident, not arrogant", "We know our data is good. We don't oversell."),
            ("Technical, not jargon-heavy", "Use proper trading terms, but always be clear."),
            ("Helpful, not patronizing", "Guide users, don't lecture them."),
            ("Concise, not terse", "Every word earns its place. No filler."),
        ]
        for title, desc in tone_items:
            self._check_space(15)
            y = self.get_y()
            self.set_font("Helvetica", "B", 10)
            self.set_text_color(*CYAN)
            self.set_xy(24, y)
            self.cell(60, 6, title)
            self.set_font("Helvetica", "", 9.5)
            self.set_text_color(*LIGHT_GRAY)
            self.set_xy(86, y)
            self.cell(100, 6, desc)
            self.ln(7)

        self._check_space(40)
        self._subsection_title("Target Audience")
        audiences = [
            "Indian retail traders (18-45, tech-savvy, mobile-first)",
            "Swing traders looking for breakout entry points",
            "Technical analysts needing real-time NSE/BSE screener",
            "New investors wanting AI-powered stock recommendations",
            "Trading communities on Discord/Telegram/Twitter",
        ]
        for a in audiences:
            self._check_space(10)
            self._bullet_point(a, bullet_color=CYAN)

    def build_logo_system(self):
        self.add_page()
        self._draw_page_bg()
        self._page_number_footer()
        self._section_title(2, "Logo System")

        self._subsection_title("Primary Logo")
        self._body_text(
            "The BreakoutScan logo combines a stylized 'B' lettermark with a breakout chart pattern, "
            "symbolizing the moment a stock breaks above resistance. The mark is set in Electric Purple "
            "(#7C5CFC) to convey premium fintech identity."
        )

        y = self.get_y() + 5
        # Dark bg logo
        self.set_fill_color(*DARK_CARD)
        self.set_draw_color(*SECTION_BORDER)
        self.set_line_width(0.3)
        self.rect(20, y, 80, 50, "DF")
        self.set_fill_color(*ACCENT)
        self.ellipse(40, y + 10, 30, 30, "F")
        self.set_font("Helvetica", "B", 20)
        self.set_text_color(*WHITE)
        self.set_xy(40, y + 14)
        self.cell(30, 22, "BS", align="C")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*MID_GRAY)
        self.set_xy(20, y + 42)
        self.cell(80, 6, "Primary Logo -- Dark Background", align="C")

        # Light bg logo
        self.set_fill_color(*LIGHT_BG)
        self.set_draw_color(*LIGHT_GRAY)
        self.rect(110, y, 80, 50, "DF")
        self.set_fill_color(*ACCENT)
        self.ellipse(130, y + 10, 30, 30, "F")
        self.set_font("Helvetica", "B", 20)
        self.set_text_color(*WHITE)
        self.set_xy(130, y + 14)
        self.cell(30, 22, "BS", align="C")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*MID_GRAY)
        self.set_xy(110, y + 42)
        self.cell(80, 6, "Primary Logo -- Light Background", align="C")

        self.set_y(y + 58)

        self._subsection_title("Logo Wordmark")
        self._body_text(
            "The wordmark 'BreakoutScan' uses Inter Bold. The 'Breakout' portion is accent purple, "
            "'Scan' is white/dark to create visual distinction."
        )

        y = self.get_y() + 3
        self.set_fill_color(*DARK_CARD)
        self.set_draw_color(*SECTION_BORDER)
        self.rect(20, y, 170, 30, "DF")
        self.set_font("Helvetica", "B", 24)
        self.set_text_color(*ACCENT)
        self.set_xy(30, y + 5)
        self.cell(0, 20, "Breakout")
        self.set_text_color(*WHITE)
        self.set_xy(96, y + 5)
        self.cell(0, 20, "Scan")
        self.set_y(y + 36)

        self._subsection_title("Clear Space Rules")
        self._body_text(
            "Maintain minimum clear space equal to the height of the 'B' in the logomark around all "
            "sides. This ensures the logo remains visually prominent and uncluttered."
        )

        y = self.get_y() + 3
        self.set_fill_color(18, 24, 38)
        self.rect(50, y, 110, 60, "F")
        self.set_draw_color(*ACCENT)
        self.set_line_width(0.3)
        self.dashed_line(65, y + 10, 145, y + 10, 2, 2)
        self.dashed_line(65, y + 50, 145, y + 50, 2, 2)
        self.dashed_line(65, y + 10, 65, y + 50, 2, 2)
        self.dashed_line(145, y + 10, 145, y + 50, 2, 2)
        self.set_fill_color(*ACCENT)
        self.ellipse(90, y + 18, 24, 24, "F")
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(*WHITE)
        self.set_xy(90, y + 21)
        self.cell(24, 18, "BS", align="C")
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*ACCENT_HOVER)
        for pos in [(72, y + 27), (122, y + 27), (97, y + 11), (97, y + 44)]:
            self.set_xy(*pos)
            self.cell(15, 5, "X", align="C")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*MID_GRAY)
        self.set_xy(50, y + 52)
        self.cell(110, 6, "Minimum clear space = 1x height of logomark", align="C")
        self.set_y(y + 66)

        self._check_space(50)
        self._subsection_title("Minimum Size")
        self._table(
            ["Context", "Min Width", "Min Height", "Format"],
            [
                ["Digital (web/app)", "80px", "24px", "SVG / PNG @2x"],
                ["Social media avatar", "48px", "48px", "PNG @2x"],
                ["Print (business card)", "20mm", "10mm", "Vector PDF"],
                ["Favicon", "32px", "32px", "ICO / PNG"],
                ["App icon", "1024px", "1024px", "PNG (Apple/Google)"],
            ],
            [42, 38, 38, 52]
        )

        self._check_space(50)
        self._subsection_title("Incorrect Logo Usage")
        dont_items = [
            "Do NOT stretch or distort the logo proportions",
            "Do NOT change the logo colors outside the approved palette",
            "Do NOT place the logo on busy or low-contrast backgrounds",
            "Do NOT add drop shadows, outlines, or 3D effects",
            "Do NOT rotate the logo at any angle",
            "Do NOT crop or partially hide the logomark",
        ]
        for item in dont_items:
            self._check_space(10)
            self._bullet_point(item, bullet_color=BEARISH)

    def build_color_system(self):
        self.add_page()
        self._draw_page_bg()
        self._page_number_footer()
        self._section_title(3, "Color System")

        self._body_text(
            "The BreakoutScan color system is built on CSS custom properties, enabling seamless dark/light "
            "theme switching. Every color serves a functional purpose."
        )

        self._subsection_title("Primary Colors")
        y = self.get_y() + 3
        colors_primary = [
            (ACCENT, "Electric Purple", "#7C5CFC"),
            (CYAN, "Cyan Blue", "#00D4FF"),
            (BULLISH, "Emerald Green", "#00C796"),
            (BEARISH, "Coral Red", "#FF5A8A"),
        ]
        x = 24
        for color, name, hex_code in colors_primary:
            self._draw_color_swatch(x, y, 22, color, name, hex_code)
            x += 42
        self.set_y(y + 36)

        self._check_space(50)
        self._subsection_title("Secondary Colors")
        y = self.get_y() + 3
        colors_secondary = [
            (WARNING, "Warning Orange", "#FF8800"),
            (INFO, "Info Cyan", "#00D4FF"),
            (SOFT_PURPLE, "Soft Purple", "#5E48C0"),
            ((251, 191, 36), "Amber Gold", "#FBBF24"),
        ]
        x = 24
        for color, name, hex_code in colors_secondary:
            self._draw_color_swatch(x, y, 22, color, name, hex_code)
            x += 42
        self.set_y(y + 36)

        self._check_space(60)
        self._subsection_title("Background Colors -- Dark Mode")
        self._table(
            ["Token", "HEX / RGBA", "RGB", "Usage"],
            [
                ["--bg-page", "#0A0E1A", "10, 14, 26", "Page background"],
                ["--bg-sidebar", "rgba(16,22,36,0.85)", "16, 22, 36", "Sidebar panel"],
                ["--bg-card", "rgba(22,29,45,0.75)", "22, 29, 45", "Card surfaces"],
                ["--bg-elevated", "rgba(28,35,51,0.8)", "28, 35, 51", "Topbar, hover"],
            ],
            [40, 50, 35, 45]
        )

        self._check_space(60)
        self._subsection_title("Background Colors -- Light Mode")
        self._table(
            ["Token", "HEX / RGBA", "RGB", "Usage"],
            [
                ["--bg-page", "#F0F2F8", "240, 242, 248", "Page background"],
                ["--bg-sidebar", "rgba(255,255,255,0.7)", "255, 255, 255", "Sidebar panel"],
                ["--bg-card", "rgba(255,255,255,0.6)", "255, 255, 255", "Card surfaces"],
                ["--bg-elevated", "rgba(255,255,255,0.8)", "255, 255, 255", "Topbar, hover"],
            ],
            [40, 50, 35, 45]
        )

        self._check_space(60)
        self._subsection_title("Semantic Colors")
        self._table(
            ["Token", "Dark Mode", "Light Mode", "Usage"],
            [
                ["--bullish", "#00C796", "#00A878", "Price up, buy signals"],
                ["--bearish", "#FF5A8A", "#E5395F", "Price down, sell"],
                ["--warning", "#FF8800", "#E67E00", "Warnings, caution"],
                ["--info", "#00D4FF", "#0097CC", "Info highlights"],
                ["--accent", "#7C5CFC", "#7C5CFC", "Buttons, links"],
                ["--accent-hover", "#9B7FFF", "#6A48E8", "Hover state"],
            ],
            [38, 38, 38, 56]
        )

        self._check_space(60)
        self._subsection_title("Text Colors")
        self._table(
            ["Token", "Dark Mode", "Light Mode", "Usage"],
            [
                ["--text-primary", "#E8ECF4", "#1A1F2E", "Headings, body"],
                ["--text-secondary", "#8B95A8", "#666A7A", "Labels, secondary"],
                ["--text-muted", "#5A6478", "#9CA3B0", "Placeholders"],
            ],
            [42, 38, 38, 52]
        )

        self._check_space(50)
        self._subsection_title("Chart & Signal Colors")
        self._table(
            ["Token", "Dark", "Light", "Usage"],
            [
                ["--chart-grid", "#1A2235", "#E0E4EC", "Chart grid lines"],
                ["--chart-cross", "#7C5CFC", "#7C5CFC", "Crosshair"],
            ],
            [42, 38, 38, 52]
        )

        self._check_space(60)
        self._subsection_title("Signal Badge Colors")
        self._table(
            ["Signal", "Background", "Text Color", "Border"],
            [
                ["BREAKOUT", "purple-500/20", "purple-400", "purple-500/30"],
                ["RSI", "cyan-500/20", "cyan-400", "cyan-500/30"],
                ["EMA", "orange-500/20", "orange-400", "orange-500/30"],
                ["MACD", "yellow-500/20", "yellow-400", "yellow-500/30"],
                ["VOLUME", "emerald-500/20", "emerald-400", "emerald-500/30"],
                ["PATTERN", "blue-500/20", "blue-400", "blue-500/30"],
            ],
            [38, 44, 44, 44]
        )

        self._check_space(60)
        self._subsection_title("Gradient System")
        self._body_text("Primary gradients used across the interface:")
        y = self.get_y() + 3
        self._draw_gradient_rect(24, y, 162, 18, ACCENT, CYAN, vertical=False)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*WHITE)
        self.set_xy(24, y + 4)
        self.cell(162, 10, "Primary Gradient:  #7C5CFC  -->  #00D4FF", align="C")
        self._draw_gradient_rect(24, y + 24, 162, 18, ACCENT, BULLISH, vertical=False)
        self.set_xy(24, y + 28)
        self.cell(162, 10, "Accent Gradient:  #7C5CFC  -->  #00C796", align="C")
        self._draw_gradient_rect(24, y + 48, 162, 18, DARK_BG, DARK_CARD, vertical=False)
        self.set_xy(24, y + 52)
        self.cell(162, 10, "Background Gradient:  #0A0E1A  -->  #161D2D", align="C")
        self.set_y(y + 72)

    def build_typography(self):
        self.add_page()
        self._draw_page_bg()
        self._page_number_footer()
        self._section_title(4, "Typography System")

        self._body_text(
            "BreakoutScan uses a dual-font system: Inter for all UI text and JetBrains Mono for "
            "financial data. This ensures maximum readability for both prose and numbers."
        )

        self._subsection_title("Font Families")
        self._table(
            ["Font", "Weight Range", "Usage", "CSS Variable"],
            [
                ["Inter", "400-700", "All UI: headings, body, labels", "--font-inter"],
                ["JetBrains Mono", "400-600", "Prices, %, volumes, code", "--font-jetbrains-mono"],
            ],
            [40, 30, 60, 40]
        )

        self._check_space(50)
        self._subsection_title("Type Scale")
        scales = [
            ("H1 -- Page Title", 22, "B", "24px / text-2xl / font-bold"),
            ("H2 -- Section", 17, "B", "18-20px / text-lg sm:text-xl / semibold"),
            ("H3 -- Card Title", 14, "B", "16px / text-base / font-semibold"),
            ("Body Text", 11, "", "14px / text-sm / font-normal"),
            ("Table Header", 9, "B", "11-12px / text-xs / font-medium uppercase"),
            ("Label", 8.5, "B", "12px / text-xs / font-medium uppercase"),
            ("Caption", 8, "", "10-12px / text-[10px] / font-normal"),
        ]
        for label, size, style, spec in scales:
            self._check_space(14)
            y = self.get_y()
            self.set_font("Helvetica", style, size)
            self.set_text_color(*WHITE)
            self.set_xy(24, y)
            self.cell(80, 8, label)
            self.set_font("Courier", "", 7.5)
            self.set_text_color(*MID_GRAY)
            self.set_xy(110, y + 1)
            self.cell(80, 6, spec)
            self.set_draw_color(*SECTION_BORDER)
            self.set_line_width(0.1)
            self.line(24, y + 10, 190, y + 10)
            self.set_y(y + 13)

        self._check_space(40)
        self._subsection_title("Numeric Display")
        self._body_text("All financial numbers MUST use JetBrains Mono with tabular-nums:")
        self._code_block(
            'className="font-mono tabular-nums"\n\n'
            "Example values:\n"
            "  Price:    2,456.75\n"
            "  Change:   +3.24%\n"
            "  Volume:   12,45,678\n"
            "  RSI:      67.3"
        )

        self._check_space(50)
        self._subsection_title("Line Height & Letter Spacing")
        self._table(
            ["Element", "Line Height", "Letter Spacing", "Notes"],
            [
                ["Headings (H1-H3)", "1.2", "Normal", "Tight for impact"],
                ["Body text", "1.5-1.6", "Normal", "Comfortable reading"],
                ["Table headers", "1.2", "0.05em (wider)", "uppercase tracking"],
                ["Labels", "1.2", "0.05em (wider)", "uppercase tracking"],
                ["Code/numbers", "1.4", "Normal", "Monospace alignment"],
            ],
            [42, 32, 36, 60]
        )

        self._check_space(40)
        self._subsection_title("Responsive Scaling")
        self._table(
            ["Element", "Mobile (< 640px)", "Tablet (640px+)", "Desktop (1024px+)"],
            [
                ["H1", "text-xl (20px)", "text-2xl (24px)", "text-2xl (24px)"],
                ["H2", "text-lg (18px)", "text-xl (20px)", "text-xl (20px)"],
                ["Body", "text-sm (14px)", "text-sm (14px)", "text-sm (14px)"],
                ["Table header", "text-[11px]", "text-xs (12px)", "text-xs (12px)"],
            ],
            [34, 46, 46, 44]
        )

    def build_spacing(self):
        self.add_page()
        self._draw_page_bg()
        self._page_number_footer()
        self._section_title(5, "Spacing System")

        self._body_text(
            "BreakoutScan uses a 4px base grid. Every margin, padding, and gap is a multiple of 4px."
        )

        self._subsection_title("4px Base Scale")
        y = self.get_y() + 5
        spacing_values = [4, 6, 8, 12, 16, 20, 24, 32, 48, 64]
        tw_map = {4: "gap-1", 6: "gap-1.5", 8: "gap-2", 12: "gap-3", 16: "p-4 / gap-4",
                  20: "p-5", 24: "p-6", 32: "gap-8", 48: "gap-12", 64: "gap-16"}
        for val in spacing_values:
            self.set_font("Courier", "B", 9)
            self.set_text_color(*ACCENT_HOVER)
            self.set_xy(24, y)
            self.cell(20, 6, f"{val}px")
            bar_width = min(val * 1.8, 130)
            self.set_fill_color(*ACCENT)
            self.rect(50, y + 1, bar_width, 5, "F")
            self.set_font("Courier", "", 7.5)
            self.set_text_color(*MID_GRAY)
            self.set_xy(50 + bar_width + 4, y)
            self.cell(40, 6, tw_map.get(val, ""))
            y += 10
        self.set_y(y + 5)

        self._check_space(60)
        self._subsection_title("Component Spacing Rules")
        self._table(
            ["Context", "Token", "Value", "Notes"],
            [
                ["Icon to text", "gap-1.5", "6px", "Tight inline spacing"],
                ["Label to input", "gap-2", "8px", "Form field spacing"],
                ["Card sections", "gap-3", "12px", "Internal card areas"],
                ["Card padding (mobile)", "p-4", "16px", "Mobile card padding"],
                ["Card padding (desktop)", "p-5", "20px", "Desktop card padding"],
                ["Modal padding", "p-5 / p-6", "20-24px", "Mobile / desktop"],
                ["Grid gaps", "gap-4", "16px", "Between cards"],
                ["Section gaps", "gap-6 / gap-8", "24-32px", "Between sections"],
            ],
            [42, 30, 26, 72]
        )

    def build_grid_system(self):
        self.add_page()
        self._draw_page_bg()
        self._page_number_footer()
        self._section_title(6, "Grid System")

        self._body_text(
            "BreakoutScan uses CSS Grid and Flexbox with Tailwind responsive utilities. "
            "Sidebar + main content on desktop, single-column with bottom nav on mobile."
        )

        # Desktop
        self._subsection_title("Desktop Grid (1024px+)")
        y = self.get_y() + 3
        self.set_fill_color(18, 24, 38)
        self.set_draw_color(*SECTION_BORDER)
        self.set_line_width(0.3)
        self.rect(20, y, 170, 80, "DF")
        self.set_fill_color(16, 22, 36)
        self.rect(20, y, 35, 80, "DF")
        self.set_font("Helvetica", "B", 7)
        self.set_text_color(*ACCENT)
        self.set_xy(22, y + 3)
        self.cell(31, 5, "SIDEBAR")
        self.set_font("Helvetica", "", 6)
        self.set_text_color(*MID_GRAY)
        for i, item in enumerate(["Dashboard", "Screener", "AI Picks", "Charts", "Settings"]):
            self.set_xy(24, y + 12 + i * 8)
            self.cell(28, 5, item)
        self.set_fill_color(28, 35, 51)
        self.rect(55, y, 135, 12, "DF")
        self.set_font("Helvetica", "B", 7)
        self.set_text_color(*WHITE)
        self.set_xy(58, y + 3)
        self.cell(50, 6, "TOPBAR")
        self.set_draw_color(*ACCENT)
        self.set_line_width(0.1)
        col_w = 130 / 12
        for i in range(13):
            xc = 58 + col_w * i
            self.dashed_line(xc, y + 14, xc, y + 78, 1, 2)
        self.set_fill_color(*DARK_CARD)
        self.set_draw_color(*SECTION_BORDER)
        self.set_line_width(0.3)
        self.rect(60, y + 18, 60, 25, "DF")
        self.rect(125, y + 18, 58, 25, "DF")
        self.rect(60, y + 48, 123, 25, "DF")
        self.set_font("Helvetica", "", 6)
        self.set_text_color(*ACCENT_HOVER)
        self.set_xy(62, y + 20)
        self.cell(50, 4, "Card (6 cols)")
        self.set_xy(127, y + 20)
        self.cell(50, 4, "Card (6 cols)")
        self.set_xy(62, y + 50)
        self.cell(50, 4, "Card (12 cols)")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*MID_GRAY)
        self.set_xy(20, y + 82)
        self.cell(170, 5, "12-column grid  |  Gutter: 16px  |  Margin: 20px  |  Sidebar: 240px", align="C")
        self.set_y(y + 92)

        # Mobile
        self._check_space(90)
        self._subsection_title("Mobile Grid (< 640px)")
        y = self.get_y() + 3
        self.set_fill_color(18, 24, 38)
        self.set_draw_color(*SECTION_BORDER)
        self.rect(75, y, 60, 70, "DF")
        self.set_fill_color(28, 35, 51)
        self.rect(75, y, 60, 8, "DF")
        self.set_font("Helvetica", "B", 6)
        self.set_text_color(*WHITE)
        self.set_xy(77, y + 2)
        self.cell(50, 4, "TOPBAR")
        self.set_draw_color(*ACCENT)
        self.set_line_width(0.1)
        col_w = 56 / 4
        for i in range(5):
            xc = 77 + col_w * i
            self.dashed_line(xc, y + 10, xc, y + 58, 1, 2)
        self.set_fill_color(*DARK_CARD)
        self.set_draw_color(*SECTION_BORDER)
        self.set_line_width(0.3)
        self.rect(78, y + 12, 54, 12, "DF")
        self.rect(78, y + 28, 54, 12, "DF")
        self.rect(78, y + 44, 54, 12, "DF")
        self.set_fill_color(28, 35, 51)
        self.rect(75, y + 60, 60, 10, "DF")
        self.set_font("Helvetica", "", 5)
        self.set_text_color(*ACCENT)
        for i, item in enumerate(["Home", "Scan", "AI", "Chart"]):
            self.set_xy(77 + i * 14, y + 62)
            self.cell(14, 6, item, align="C")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*MID_GRAY)
        self.set_xy(75, y + 72)
        self.cell(60, 5, "4-col  |  Gap: 12px  |  Margin: 16px", align="C")
        self.set_y(y + 82)

        self._check_space(50)
        self._subsection_title("Responsive Breakpoints")
        self._table(
            ["Breakpoint", "Width", "Columns", "Gutter", "Margin", "Sidebar"],
            [
                ["Default (mobile)", "0px+", "4", "12px", "16px", "Hidden"],
                ["sm (tablet)", "640px+", "8", "16px", "16px", "Hamburger"],
                ["md (small desktop)", "768px+", "12", "16px", "20px", "Visible"],
                ["lg (desktop)", "1024px+", "12", "16px", "24px", "Visible"],
            ],
            [34, 22, 20, 22, 22, 50]
        )

    def build_components(self):
        self.add_page()
        self._draw_page_bg()
        self._page_number_footer()
        self._section_title(7, "UI Components")

        self._body_text(
            "All UI components follow a consistent design language with glassmorphic surfaces, "
            "accent-colored interactions, and accessibility-first states."
        )

        # Buttons
        self._subsection_title("Buttons")
        y = self.get_y() + 5
        self._draw_gradient_rect(24, y, 80, 14, ACCENT, SOFT_PURPLE, vertical=False)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*WHITE)
        self.set_xy(24, y + 2)
        self.cell(80, 10, "Apply Filters", align="C")
        self.set_draw_color(*ACCENT)
        self.set_line_width(0.5)
        self.set_fill_color(*DARK_BG)
        self.rect(112, y, 76, 14, "DF")
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*ACCENT)
        self.set_xy(112, y + 2)
        self.cell(76, 10, "Cancel", align="C")
        self.set_y(y + 20)

        self.set_fill_color(*DARK_ELEVATED)
        self.rect(24, self.get_y(), 60, 14, "F")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*MID_GRAY)
        self.set_xy(24, self.get_y() + 2)
        self.cell(60, 10, "Close", align="C")
        self.set_fill_color(35, 40, 55)
        self.rect(92, self.get_y() - 2, 80, 14, "F")
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*MUTED)
        self.set_xy(92, self.get_y())
        self.cell(80, 10, "Disabled", align="C")
        self.set_y(self.get_y() + 18)

        self._table(
            ["Variant", "Background", "Text", "Border", "Usage"],
            [
                ["Primary", "Purple gradient", "White", "None", "Primary CTAs"],
                ["Secondary", "Transparent", "Accent", "Accent", "Secondary"],
                ["Ghost", "Elevated hover", "Secondary", "None", "Tertiary"],
                ["Disabled", "Muted bg", "Muted text", "None", "Unavailable"],
            ],
            [28, 38, 26, 26, 52]
        )

        self._table(
            ["Size", "Height", "Padding", "Font Size"],
            [
                ["Small", "36px (h-9)", "px-3", "12px (text-xs)"],
                ["Medium", "40-44px (h-10/11)", "px-4 sm:px-5", "14px (text-sm)"],
                ["Large", "48px (h-12)", "px-6", "16px (text-base)"],
            ],
            [30, 46, 46, 48]
        )

        # Cards
        self._check_space(60)
        self._subsection_title("Cards")
        y = self.get_y() + 3

        self.set_fill_color(*DARK_CARD)
        self.set_draw_color(*SECTION_BORDER)
        self.set_line_width(0.3)
        self.rect(24, y, 75, 45, "DF")
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*WHITE)
        self.set_xy(30, y + 6)
        self.cell(60, 5, "Card Title")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*MID_GRAY)
        self.set_xy(30, y + 14)
        self.cell(60, 4, "Subtitle text here")
        self.set_font("Courier", "B", 14)
        self.set_text_color(*BULLISH)
        self.set_xy(30, y + 24)
        self.cell(60, 8, "+2.45%")
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*MUTED)
        self.set_xy(30, y + 36)
        self.cell(60, 4, "Live data feed")

        self.set_fill_color(*DARK_CARD)
        self.set_draw_color(*ACCENT)
        self.set_line_width(0.5)
        self.rect(108, y, 75, 45, "DF")
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*WHITE)
        self.set_xy(114, y + 6)
        self.cell(60, 5, "Card (Hover State)")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*MID_GRAY)
        self.set_xy(114, y + 14)
        self.cell(60, 4, "translateY(-2px)")
        self.set_font("Courier", "B", 14)
        self.set_text_color(*BEARISH)
        self.set_xy(114, y + 24)
        self.cell(60, 8, "-1.32%")
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*ACCENT_HOVER)
        self.set_xy(114, y + 36)
        self.cell(60, 4, "Accent glow border")
        self.set_y(y + 52)

        self._body_text(
            "Cards use glassmorphic backgrounds. On hover, they lift 2px with accent border glow. "
            "Border radius 12px. Padding: 16px mobile / 20px desktop."
        )

        # Badges
        self._check_space(50)
        self._subsection_title("Badges")
        y = self.get_y() + 3
        badges = [
            (BULLISH, "BULLISH"), (BEARISH, "BEARISH"), (WARNING, "WARNING"),
            (ACCENT, "BREAKOUT"), (CYAN, "RSI"), (MID_GRAY, "NEUTRAL"),
        ]
        x = 24
        for color, label in badges:
            bg_c = (color[0] // 5 + 10, color[1] // 5 + 10, color[2] // 5 + 10)
            self.set_fill_color(*bg_c)
            self.set_draw_color(*color)
            self.set_line_width(0.4)
            w = len(label) * 3.5 + 10
            self.rect(x, y, w, 10, "DF")
            self.set_font("Helvetica", "B", 7)
            self.set_text_color(*color)
            self.set_xy(x, y + 1.5)
            self.cell(w, 7, label, align="C")
            x += w + 5
            if x > 170:
                x = 24
                y += 14
        self.set_y(y + 16)

        # Inputs
        self._check_space(50)
        self._subsection_title("Inputs")
        y = self.get_y() + 3
        self.set_font("Helvetica", "B", 7)
        self.set_text_color(*MID_GRAY)
        self.set_xy(24, y)
        self.cell(40, 4, "STOCK SYMBOL")
        self.set_fill_color(10, 14, 26)
        self.set_draw_color(*SECTION_BORDER)
        self.set_line_width(0.3)
        self.rect(24, y + 5, 75, 12, "DF")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*MUTED)
        self.set_xy(28, y + 7.5)
        self.cell(70, 7, "Search stocks...")
        self.set_font("Helvetica", "B", 7)
        self.set_text_color(*ACCENT)
        self.set_xy(108, y)
        self.cell(40, 4, "STOCK SYMBOL")
        self.set_fill_color(10, 14, 26)
        self.set_draw_color(*ACCENT)
        self.set_line_width(0.5)
        self.rect(108, y + 5, 75, 12, "DF")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*WHITE)
        self.set_xy(112, y + 7.5)
        self.cell(70, 7, "RELIANCE")
        self.set_y(y + 24)

        # Modal
        self._check_space(50)
        self._subsection_title("Modals")
        self._table(
            ["Property", "Mobile", "Desktop"],
            [
                ["Style", "Bottom sheet", "Centered dialog"],
                ["Border radius", "16px top only", "16px all corners"],
                ["Backdrop", "bg-black/70 blur", "bg-black/70 blur"],
                ["Max height", "80vh", "85vh"],
                ["Animation", "Slide up", "Scale + fade"],
                ["Close", "Drag / tap / ESC", "Click / ESC"],
            ],
            [42, 64, 64]
        )

        # Data Table
        self._check_space(50)
        self._subsection_title("Data Tables")
        self._body_text("Sortable columns, alternating rows, staggered fade-in (50ms/row):")
        self._table(
            ["Symbol", "Price", "Change %", "Volume", "Signal"],
            [
                ["RELIANCE", "2,456.75", "+3.24%", "12,45,678", "BREAKOUT"],
                ["TCS", "3,789.50", "-1.02%", "8,34,521", "RSI"],
                ["INFY", "1,567.30", "+2.15%", "15,67,890", "EMA"],
                ["HDFCBANK", "1,823.45", "+0.87%", "6,78,234", "VOLUME"],
            ],
            [34, 34, 34, 34, 34]
        )

        # Navigation, Tooltips, Dropdowns, Tabs
        self._check_space(30)
        self._subsection_title("Navigation")
        self._body_text(
            "Desktop: Fixed left sidebar (240px), glassmorphic. Mobile: Bottom tab bar with 5 items."
        )
        self._check_space(30)
        self._subsection_title("Tooltips & Dropdowns")
        self._body_text(
            "Tooltips: elevated bg, rounded-lg (8px), fade-in, max-width 200px. "
            "Dropdowns: card bg, shadow-2xl, 8px padding, hover elevated bg."
        )
        self._check_space(30)
        self._subsection_title("Tabs")
        self._body_text(
            "Underline style with 2px accent bottom border on active. Inactive: text-secondary. "
            "Transition: 200ms ease."
        )

    def build_iconography(self):
        self.add_page()
        self._draw_page_bg()
        self._page_number_footer()
        self._section_title(8, "Iconography")

        self._body_text("BreakoutScan uses Lucide React -- clean, consistent, open-source, 1000+ icons.")

        self._subsection_title("Icon System Specs")
        self._table(
            ["Property", "Value", "Notes"],
            [
                ["Library", "Lucide React", "lucide.dev"],
                ["Style", "Outline (stroke)", "Consistent with UI"],
                ["Stroke width", "2px (default)", "Matches border weights"],
                ["Default size", "20px (h-5 w-5)", "Action icons"],
                ["Small size", "12px (h-3 w-3)", "Inline indicators"],
                ["Large size", "24px (h-6 w-6)", "Navigation emphasis"],
                ["Color", "currentColor", "Inherits text color"],
                ["Export format", "SVG (inline React)", "Tree-shakeable"],
            ],
            [42, 52, 76]
        )

        self._check_space(50)
        self._subsection_title("Common Icon Usage")
        self._table(
            ["Context", "Icon(s)", "Size", "Color"],
            [
                ["Sort column", "ArrowUpDown/Up/Down", "12px", "--text-secondary"],
                ["Close modal", "X", "20px", "--text-secondary"],
                ["Navigation", "Various Lucide", "20px", "--accent (active)"],
                ["Bullish", "TrendingUp", "16px", "--bullish"],
                ["Bearish", "TrendingDown", "16px", "--bearish"],
                ["Search", "Search", "20px", "--text-muted"],
                ["Settings", "Settings", "20px", "--text-secondary"],
                ["Theme toggle", "Sun / Moon", "20px", "--accent"],
                ["Refresh", "RefreshCw", "20px", "--accent"],
            ],
            [38, 48, 30, 54]
        )

    def build_glassmorphism(self):
        self.add_page()
        self._draw_page_bg()
        self._page_number_footer()
        self._section_title(9, "Glassmorphism")

        self._body_text(
            "Glassmorphism is the core visual identity. Frosted glass panels create depth hierarchy."
        )

        self._subsection_title("Glass Panel Types")
        self._table(
            ["Class", "Blur", "Background", "Border", "Usage"],
            [
                [".glass", "12px", "var(--glass-bg)", "glass-border", "Generic"],
                [".glass-card", "16px", "var(--bg-card)", "--border", "Content cards"],
                [".glass-sidebar", "20px", "var(--bg-sidebar)", "Right border", "Navigation"],
                [".glass-topbar", "16px", "var(--bg-elevated)", "Bottom border", "Top nav"],
            ],
            [30, 18, 38, 38, 46]
        )

        self._check_space(60)
        self._subsection_title("Glass Effect Demo")
        y = self.get_y() + 3
        self._draw_gradient_rect(20, y, 170, 55, (15, 18, 35), (20, 28, 50))
        self.set_fill_color(22, 29, 45)
        self.set_draw_color(55, 65, 90)
        self.set_line_width(0.3)
        self.rect(35, y + 8, 140, 38, "DF")
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*WHITE)
        self.set_xy(42, y + 13)
        self.cell(120, 8, "Glass Card Panel")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*MID_GRAY)
        self.set_xy(42, y + 22)
        self.cell(120, 5, "backdrop-filter: blur(16px)")
        self.set_xy(42, y + 28)
        self.cell(120, 5, "background: rgba(22, 29, 45, 0.75)")
        self.set_xy(42, y + 34)
        self.cell(120, 5, "border: 1px solid rgba(35, 45, 64, 0.6)")
        self.set_y(y + 62)

        self._check_space(40)
        self._subsection_title("Card Hover Glow")
        self._code_block(
            ".glass-card:hover {\n"
            "  box-shadow: 0 0 24px var(--accent-glow),\n"
            "              var(--glass-shadow);\n"
            "  border-color: rgba(124, 92, 252, 0.2);\n"
            "  transform: translateY(-2px);\n"
            "  transition: all 200ms ease-out;\n"
            "}"
        )

        self._check_space(40)
        self._subsection_title("Ambient Glow")
        self._code_block(
            ".ambient-glow::before {\n"
            "  content: '';\n"
            "  position: absolute;\n"
            "  inset: -4px;\n"
            "  background: linear-gradient(135deg,\n"
            "    rgba(124, 92, 252, 0.15),\n"
            "    rgba(0, 212, 255, 0.08));\n"
            "  filter: blur(12px);\n"
            "  border-radius: inherit;\n"
            "  opacity: 0;\n"
            "  transition: opacity 300ms ease;\n"
            "}\n"
            ".ambient-glow:hover::before {\n"
            "  opacity: 1;\n"
            "}"
        )

        self._check_space(50)
        self._subsection_title("Page Background Gradients")
        self._code_block(
            "/* Dark Mode */\n"
            "background:\n"
            "  radial-gradient(ellipse at 20% 0%,\n"
            "    rgba(124, 92, 252, 0.08), transparent 50%),\n"
            "  radial-gradient(ellipse at 80% 100%,\n"
            "    rgba(0, 212, 255, 0.04), transparent 50%),\n"
            "  linear-gradient(180deg,\n"
            "    #0c1020 0%, #0a0e1a 40%, #080c16 100%);\n"
            "\n"
            "/* Light Mode */\n"
            "background:\n"
            "  radial-gradient(ellipse at 0% 0%,\n"
            "    rgba(124, 92, 252, 0.12), transparent 50%),\n"
            "  radial-gradient(ellipse at 100% 0%,\n"
            "    rgba(236, 72, 153, 0.08), transparent 50%),\n"
            "  linear-gradient(180deg,\n"
            "    #e8eaf4 0%, #f0f2f8 40%, #f5f6fc 100%);"
        )

    def build_shadows(self):
        self.add_page()
        self._draw_page_bg()
        self._page_number_footer()
        self._section_title(10, "Shadows & Elevation")

        self._body_text(
            "Darker, larger shadows = higher elevation. Accent shadows add brand color to CTAs."
        )

        self._subsection_title("Shadow Tokens")
        self._table(
            ["Token", "Value", "Usage"],
            [
                ["shadow-card", "0 4px 24px rgba(0,0,0,0.5)", "Default card"],
                ["shadow-accent", "0 4px 20px rgba(124,92,252,0.25)", "Primary button"],
                ["shadow-glow", "0 0 20px rgba(124,92,252,0.15)", "Card hover"],
                ["--glass-shadow", "0 8px 32px rgba(0,0,0,0.4)", "Glass panel"],
                ["shadow-2xl", "Tailwind default", "Modal shadow"],
            ],
            [38, 80, 52]
        )

        self._check_space(50)
        self._subsection_title("Elevation Hierarchy")
        levels = [
            ("Level 0", "Page Background", "--bg-page", DARK_BG),
            ("Level 1", "Card Surface", "--bg-card + shadow", DARK_CARD),
            ("Level 2", "Sidebar / Topbar", "--bg-sidebar", DARK_ELEVATED),
            ("Level 3", "Modal Overlay", "bg-black/70 + blur", (0, 0, 0)),
            ("Level 4", "Modal Content", "--bg-card + shadow-2xl", DARK_CARD),
        ]
        for level, name, token, color in levels:
            self._check_space(14)
            y = self.get_y()
            self.set_fill_color(*color)
            self.set_draw_color(*SECTION_BORDER)
            self.set_line_width(0.3)
            self.rect(24, y, 20, 8, "DF")
            self.set_font("Helvetica", "B", 9)
            self.set_text_color(*ACCENT_HOVER)
            self.set_xy(48, y)
            self.cell(25, 8, level)
            self.set_font("Helvetica", "B", 9)
            self.set_text_color(*WHITE)
            self.set_xy(73, y)
            self.cell(40, 8, name)
            self.set_font("Courier", "", 7.5)
            self.set_text_color(*MID_GRAY)
            self.set_xy(115, y)
            self.cell(75, 8, token)
            self.set_y(y + 11)

    def build_motion(self):
        self.add_page()
        self._draw_page_bg()
        self._page_number_footer()
        self._section_title(11, "Motion Guidelines")

        self._body_text(
            "Motion serves as feedback, not decoration. All animations respect prefers-reduced-motion."
        )

        self._subsection_title("Keyframe Animations")
        self._table(
            ["Animation", "Duration", "Easing", "Description"],
            [
                ["fade-in", "300ms", "ease-out", "Opacity 0 -> 1"],
                ["slide-up", "350ms", "cubic-bezier", "translateY(12->0)"],
                ["scale-in", "200ms", "cubic-bezier", "scale(0.95->1)"],
                ["shimmer", "2s", "ease-in-out", "Loading skeleton"],
                ["glow-pulse", "infinite", "ease", "Shadow pulse"],
                ["flash-bullish", "600ms", "ease-out", "Green bg flash"],
                ["flash-bearish", "600ms", "ease-out", "Red bg flash"],
                ["pulse-dot", "1.5s", "ease-in-out", "Live status dot"],
                ["ticker-scroll", "linear", "linear", "Index ticker"],
            ],
            [35, 30, 50, 55]
        )

        self._check_space(50)
        self._subsection_title("Page Transitions")
        self._table(
            ["Phase", "Duration", "Properties"],
            [
                ["Exit", "250ms", "opacity 1->0, translateY(0 -> -8px)"],
                ["Enter", "300ms", "opacity 0->1, translateY(12px -> 0)"],
                ["Reduced motion", "0ms", "No animation"],
            ],
            [30, 30, 110]
        )

        self._check_space(50)
        self._subsection_title("Interaction Animations")
        self._table(
            ["Interaction", "Effect", "Duration"],
            [
                ["Button press", "scale(0.97)", "Instant"],
                ["Card hover", "translateY(-2px) + glow", "200ms"],
                ["Modal enter", "slideY(60->0) + fade", "250ms"],
                ["Modal exit", "slideY(0->40) + fade", "200ms"],
                ["Table row enter", "stagger 50ms", "300ms"],
                ["Theme switch", "bg 400ms, color 300ms", "300-400ms"],
                ["Price flash", "Green/red bg flash", "600ms"],
                ["Live dot", "Scale + opacity pulse", "1.5s loop"],
            ],
            [42, 70, 58]
        )

        self._check_space(30)
        self._subsection_title("Easing Curves")
        self._body_text(
            "Primary: ease-out-expo = cubic-bezier(0.16, 1, 0.3, 1) -- fast start, gentle stop."
        )

    def build_theme(self):
        self.add_page()
        self._draw_page_bg()
        self._page_number_footer()
        self._section_title(12, "Dark / Light Theme")

        self._body_text(
            "Every color is a CSS custom property controlled by data-theme on <html>."
        )

        self._subsection_title("Implementation")
        self._code_block(
            '<html data-theme="dark">  <!-- or "light" -->\n\n'
            "/* Toggled via ThemeProvider context */\n"
            "/* Meta theme-color tag also updates */\n"
            "/* Transition: background 400ms, color 300ms */"
        )

        self._check_space(80)
        self._subsection_title("Theme Comparison")
        self._table(
            ["Element", "Dark Mode", "Light Mode"],
            [
                ["Page bg", "#0A0E1A (deep navy)", "#F0F2F8 (soft lavender)"],
                ["Cards", "Dark translucent", "White translucent"],
                ["Accent hover", "#9B7FFF (lighter)", "#6A48E8 (darker)"],
                ["Bullish", "#00C796 (bright)", "#00A878 (muted)"],
                ["Bearish", "#FF5A8A (bright)", "#E5395F (muted)"],
                ["Shadows", "Heavy, dark", "Light, subtle"],
                ["Glass border", "Purple-tinted", "Gray-tinted"],
                ["color-scheme", "dark", "light"],
                ["Text primary", "#E8ECF4 (light)", "#1A1F2E (dark)"],
            ],
            [36, 67, 67]
        )

        # Visual comparison
        self._check_space(60)
        self._subsection_title("Visual Comparison")
        y = self.get_y() + 3
        # Dark
        self.set_fill_color(*DARK_BG)
        self.rect(20, y, 82, 45, "F")
        self.set_fill_color(*DARK_CARD)
        self.set_draw_color(*SECTION_BORDER)
        self.set_line_width(0.3)
        self.rect(26, y + 6, 70, 32, "DF")
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*WHITE)
        self.set_xy(30, y + 9)
        self.cell(60, 5, "NIFTY 50")
        self.set_font("Courier", "B", 12)
        self.set_text_color(*BULLISH)
        self.set_xy(30, y + 17)
        self.cell(60, 8, "22,456.75  +1.2%")
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*MID_GRAY)
        self.set_xy(30, y + 28)
        self.cell(60, 4, "Live  |  NSE")
        self.set_font("Helvetica", "B", 7)
        self.set_text_color(*ACCENT)
        self.set_xy(20, y + 40)
        self.cell(82, 4, "Dark Mode", align="C")
        # Light
        self.set_fill_color(*LIGHT_BG)
        self.rect(108, y, 82, 45, "F")
        self.set_fill_color(255, 255, 255)
        self.set_draw_color(*LIGHT_GRAY)
        self.rect(114, y + 6, 70, 32, "DF")
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(26, 31, 46)
        self.set_xy(118, y + 9)
        self.cell(60, 5, "NIFTY 50")
        self.set_font("Courier", "B", 12)
        self.set_text_color(0, 168, 120)
        self.set_xy(118, y + 17)
        self.cell(60, 8, "22,456.75  +1.2%")
        self.set_font("Helvetica", "", 7)
        self.set_text_color(102, 106, 122)
        self.set_xy(118, y + 28)
        self.cell(60, 4, "Live  |  NSE")
        self.set_font("Helvetica", "B", 7)
        self.set_text_color(*SOFT_PURPLE)
        self.set_xy(108, y + 40)
        self.cell(82, 4, "Light Mode", align="C")
        self.set_y(y + 52)

    def build_accessibility(self):
        self.add_page()
        self._draw_page_bg()
        self._page_number_footer()
        self._section_title(13, "Accessibility Guidelines")

        self._body_text("BreakoutScan follows WCAG 2.1 Level AA guidelines.")

        self._subsection_title("Color Contrast Ratios")
        self._table(
            ["Element", "Foreground", "Background", "Ratio", "Level"],
            [
                ["Primary text", "#E8ECF4", "#0A0E1A", "13.8:1", "AAA"],
                ["Secondary text", "#8B95A8", "#0A0E1A", "6.2:1", "AA"],
                ["Bullish green", "#00C796", "#0A0E1A", "8.1:1", "AAA"],
                ["Bearish red", "#FF5A8A", "#0A0E1A", "5.3:1", "AA"],
                ["Accent purple", "#7C5CFC", "#0A0E1A", "4.6:1", "AA"],
                ["Muted text", "#5A6478", "#0A0E1A", "3.5:1", "AA Large"],
            ],
            [34, 28, 28, 22, 58]
        )

        self._check_space(50)
        self._subsection_title("Motion Accessibility")
        for item in [
            "All animations respect prefers-reduced-motion: reduce",
            "View transitions disabled with reduced motion preferred",
            "Shimmer replaced with static loading states",
            "Price flash disabled -- color change only remains",
        ]:
            self._bullet_point(item)

        self._check_space(50)
        self._subsection_title("Focus States")
        for item in [
            "Inputs: ring-2 ring-accent/15 on :focus-visible",
            "Buttons: browser outline on :focus-visible",
            "Cards: visible focus ring on keyboard navigation",
        ]:
            self._bullet_point(item)

        self._check_space(40)
        self._subsection_title("Touch Targets")
        for item in [
            "Minimum 44px x 44px on mobile",
            "Buttons: min-height 36px (sm), 40px (md), 48px (lg)",
            "Table rows: min-height 44px on mobile",
        ]:
            self._bullet_point(item)

        self._check_space(40)
        self._subsection_title("Semantic HTML")
        for item in [
            "Modals use aria-label on close buttons",
            "Tables use proper thead, tbody, th, td structure",
            "Navigation uses <nav> landmark elements",
            "Live data uses aria-live regions for screen readers",
            "Color never sole indicator -- icons/text accompany all states",
        ]:
            self._bullet_point(item)

        self._check_space(40)
        self._subsection_title("Keyboard Navigation")
        self._table(
            ["Key", "Action"],
            [
                ["Tab", "Move focus forward"],
                ["Shift+Tab", "Move focus backward"],
                ["Enter/Space", "Activate button or link"],
                ["Escape", "Close modal or dropdown"],
                ["Arrow keys", "Navigate within lists/tabs"],
            ],
            [42, 128]
        )

    def build_responsive(self):
        self.add_page()
        self._draw_page_bg()
        self._page_number_footer()
        self._section_title(14, "Responsive Design")

        self._body_text("Mobile-first. Base styles target mobile, progressive enhancement for larger screens.")

        self._subsection_title("Mobile Optimizations")
        for item in [
            "Touch targets: Min 44px x 44px on all interactive elements",
            "Safe areas: env(safe-area-inset-*) for iPhone notch/home bar",
            "Momentum scroll: -webkit-overflow-scrolling: touch + hidden scrollbars",
            "Scroll fade hints: Horizontal scroll areas get edge fade masks",
            "Bottom sheet modals: Full-width, rounded-top, with drag handle",
            "Bottom navigation: 5-item tab bar (hidden on desktop)",
            "Haptic feedback: Press-scale effect on buttons (scale 0.97)",
        ]:
            self._check_space(10)
            self._bullet_point(item, bullet_color=CYAN)

        self._check_space(40)
        self._subsection_title("Desktop Enhancements")
        for item in [
            "Sidebar navigation visible (240px, glassmorphic)",
            "Larger card padding: p-5 (20px) vs p-4 (16px)",
            "Larger button heights: h-11 (44px) vs h-10 (40px)",
            "Centered modals with rounded-2xl (16px all corners)",
            "Multi-column grid layouts (12-column system)",
            "Hover states on cards with translateY(-2px) lift",
        ]:
            self._check_space(10)
            self._bullet_point(item, bullet_color=ACCENT)

        self._check_space(60)
        self._subsection_title("Page Layout Structure")
        self._code_block(
            "+--------------------------------------------------+\n"
            "|  Index Ticker Bar (full width, scrolling)         |\n"
            "+----------+---------------------------------------+\n"
            "|          |  Topbar (glass, blur 16px)             |\n"
            "| Sidebar  +---------------------------------------+\n"
            "| (glass,  |                                       |\n"
            "|  blur    |  Main Content Area                    |\n"
            "|  20px)   |  (page-transition animated)           |\n"
            "|          |                                       |\n"
            "|  Hidden  |  +----------+  +----------+           |\n"
            "|  on      |  | Card     |  | Card     |           |\n"
            "|  mobile  |  | (glass)  |  | (glass)  |           |\n"
            "|          |  +----------+  +----------+           |\n"
            "+----------+---------------------------------------+\n"
            "|  Mobile Bottom Nav (sm:hidden, safe-area)         |\n"
            "+--------------------------------------------------+"
        )

    def build_design_tokens(self):
        self.add_page()
        self._draw_page_bg()
        self._page_number_footer()
        self._section_title(15, "Design Tokens")

        self._body_text("Complete CSS custom properties and Tailwind config reference.")

        self._subsection_title("CSS Custom Properties -- Dark Mode")
        self._code_block(
            ':root, [data-theme="dark"] {\n'
            "  --bg-page: #0a0e1a;\n"
            "  --bg-sidebar: rgba(16, 22, 36, 0.85);\n"
            "  --bg-card: rgba(22, 29, 45, 0.75);\n"
            "  --bg-elevated: rgba(28, 35, 51, 0.8);\n"
            "  --border: rgba(35, 45, 64, 0.6);\n"
            "  --border-subtle: #1a2235;\n"
            "  --accent: #7c5cfc;\n"
            "  --accent-hover: #9b7fff;\n"
            "  --accent-glow: rgba(124, 92, 252, 0.2);\n"
            "  --bullish: #00c796;\n"
            "  --bearish: #ff5a8a;\n"
            "  --warning: #ff8800;\n"
            "  --info: #00d4ff;\n"
            "  --text-primary: #e8ecf4;\n"
            "  --text-secondary: #8b95a8;\n"
            "  --text-muted: #5a6478;\n"
            "  --glass-bg: rgba(16, 22, 36, 0.6);\n"
            "  --glass-border: rgba(124, 92, 252, 0.1);\n"
            "  --glass-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);\n"
            "  color-scheme: dark;\n"
            "}"
        )

        self._check_space(80)
        self._subsection_title("CSS Custom Properties -- Light Mode")
        self._code_block(
            '[data-theme="light"] {\n'
            "  --bg-page: #f0f2f8;\n"
            "  --bg-sidebar: rgba(255, 255, 255, 0.7);\n"
            "  --bg-card: rgba(255, 255, 255, 0.6);\n"
            "  --bg-elevated: rgba(255, 255, 255, 0.8);\n"
            "  --border: rgba(200, 205, 220, 0.5);\n"
            "  --accent: #7c5cfc;\n"
            "  --accent-hover: #6a48e8;\n"
            "  --bullish: #00a878;\n"
            "  --bearish: #e5395f;\n"
            "  --warning: #e67e00;\n"
            "  --info: #0097cc;\n"
            "  --text-primary: #1a1f2e;\n"
            "  --text-secondary: #666a7a;\n"
            "  --text-muted: #9ca3b0;\n"
            "  --glass-bg: rgba(255, 255, 255, 0.5);\n"
            "  --glass-border: rgba(200, 205, 220, 0.4);\n"
            "  color-scheme: light;\n"
            "}"
        )

        self._check_space(70)
        self._subsection_title("Tailwind Configuration")
        self._code_block(
            "// tailwind.config.ts\n"
            "module.exports = {\n"
            "  theme: {\n"
            "    extend: {\n"
            "      colors: {\n"
            "        page: 'var(--bg-page)',\n"
            "        card: 'var(--bg-card)',\n"
            "        elevated: 'var(--bg-elevated)',\n"
            "        accent: {\n"
            "          DEFAULT: 'var(--accent)',\n"
            "          hover: 'var(--accent-hover)',\n"
            "          glow: 'var(--accent-glow)',\n"
            "        },\n"
            "        bullish: 'var(--bullish)',\n"
            "        bearish: 'var(--bearish)',\n"
            "      },\n"
            "      boxShadow: {\n"
            "        card: '0 4px 24px rgba(0,0,0,0.5)',\n"
            "        accent: '0 4px 20px rgba(124,92,252,0.25)',\n"
            "        glow: '0 0 20px rgba(124,92,252,0.15)',\n"
            "      },\n"
            "      borderRadius: { panel: '12px' },\n"
            "      fontFamily: {\n"
            "        sans: ['var(--font-inter)'],\n"
            "        mono: ['var(--font-jetbrains-mono)'],\n"
            "      },\n"
            "    },\n"
            "  },\n"
            "}"
        )

        self._check_space(50)
        self._subsection_title("Figma Naming Convention")
        self._table(
            ["Category", "Pattern", "Example"],
            [
                ["Atoms", "atom/[name]/[variant]", "atom/button/primary"],
                ["Molecules", "molecule/[name]/[state]", "molecule/card/hover"],
                ["Organisms", "organism/[name]", "organism/sidebar"],
                ["Pages", "page/[name]/[viewport]", "page/screener/mobile"],
                ["Tokens", "token/[category]/[name]", "token/color/accent"],
            ],
            [36, 60, 74]
        )

    def build_file_map(self):
        self.add_page()
        self._draw_page_bg()
        self._page_number_footer()
        self._section_title(16, "Component File Map")

        self._body_text("Source file reference for all design system implementations.")

        self._table(
            ["File Path", "Purpose"],
            [
                ["globals.css", "CSS custom props, glass, animations"],
                ["tailwind.config.ts", "Token extensions (colors, shadows)"],
                ["ui/button.tsx", "Button (3 variants, 3 sizes)"],
                ["ui/card.tsx", "Card (glass, hover, glow)"],
                ["ui/badge.tsx", "Badge (5 semantic variants)"],
                ["ui/input.tsx", "Input (label, error, focus)"],
                ["ui/modal.tsx", "Modal (bottom sheet / centered)"],
                ["ui/skeleton.tsx", "Skeleton loaders (shimmer)"],
                ["ui/data-table.tsx", "Data table (sortable, animated)"],
                ["ui/section-heading.tsx", "Section heading component"],
                ["ui/live-dot.tsx", "Live status dot (ping)"],
                ["ui/price-cell.tsx", "Price cell (flash on change)"],
                ["ui/countdown-bar.tsx", "Market session progress"],
                ["shared/signal-badge.tsx", "Signal badges (6 types)"],
                ["providers/theme-provider.tsx", "Theme toggle context"],
            ],
            [68, 102]
        )

        self._check_space(40)
        self._subsection_title("Directory Structure")
        self._code_block(
            "apps/web/src/\n"
            "  app/\n"
            "    globals.css          # Design tokens + utilities\n"
            "    layout.tsx           # Root layout + providers\n"
            "  components/\n"
            "    ui/                  # Atomic design components\n"
            "      button.tsx\n"
            "      card.tsx\n"
            "      badge.tsx\n"
            "      input.tsx\n"
            "      modal.tsx\n"
            "      skeleton.tsx\n"
            "      data-table.tsx\n"
            "      section-heading.tsx\n"
            "      live-dot.tsx\n"
            "      price-cell.tsx\n"
            "      countdown-bar.tsx\n"
            "    shared/\n"
            "      signal-badge.tsx\n"
            "    providers/\n"
            "      theme-provider.tsx\n"
            "  tailwind.config.ts     # Extended tokens"
        )

    def build_closing(self):
        self.add_page()
        self._draw_page_bg()
        self._draw_accent_bar(80)

        self.set_fill_color(*ACCENT)
        self.ellipse(85, 95, 40, 40, "F")
        self.set_font("Helvetica", "B", 30)
        self.set_text_color(*WHITE)
        self.set_xy(85, 100)
        self.cell(40, 30, "BS", align="C")

        self.set_font("Helvetica", "B", 28)
        self.set_text_color(*WHITE)
        self.set_xy(0, 145)
        self.cell(210, 14, "BreakoutScan", align="C")

        self.set_font("Helvetica", "", 14)
        self.set_text_color(*ACCENT_HOVER)
        self.set_xy(0, 162)
        self.cell(210, 8, "Design System v1.0", align="C")

        self._draw_gradient_rect(60, 178, 90, 1.5, ACCENT, CYAN, vertical=False)

        self.set_font("Helvetica", "", 11)
        self.set_text_color(*MID_GRAY)
        self.set_xy(0, 190)
        self.cell(210, 7, "Created by Adarsha Chatterjee", align="C")
        self.set_xy(0, 198)
        self.cell(210, 7, "adarsha.chatterjee@gmail.com  |  @iamadarsha", align="C")
        self.set_xy(0, 212)
        self.cell(210, 7, "Next.js  |  Tailwind CSS  |  Framer Motion  |  Lucide Icons", align="C")

        self.set_xy(0, 226)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*MUTED)
        self.cell(210, 6, "March 2026  |  Version 1.0", align="C")

        self._draw_gradient_rect(20, 270, 170, 2, ACCENT, CYAN, vertical=False)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*MUTED)
        self.set_xy(0, 278)
        self.cell(210, 5, "CONFIDENTIAL  |  For internal and partner use only", align="C")

    def generate(self, output_path):
        print("Building BreakoutScan Design System PDF...")
        builders = [
            ("Cover", self.build_cover),
            ("TOC", self.build_toc),
            ("Brand Overview", self.build_brand_overview),
            ("Logo System", self.build_logo_system),
            ("Color System", self.build_color_system),
            ("Typography", self.build_typography),
            ("Spacing", self.build_spacing),
            ("Grid System", self.build_grid_system),
            ("UI Components", self.build_components),
            ("Iconography", self.build_iconography),
            ("Glassmorphism", self.build_glassmorphism),
            ("Shadows", self.build_shadows),
            ("Motion", self.build_motion),
            ("Theme", self.build_theme),
            ("Accessibility", self.build_accessibility),
            ("Responsive", self.build_responsive),
            ("Design Tokens", self.build_design_tokens),
            ("File Map", self.build_file_map),
            ("Closing", self.build_closing),
        ]
        for i, (name, builder) in enumerate(builders, 1):
            print(f"  [{i}/{len(builders)}] {name}...")
            builder()

        self.output(output_path)
        print(f"\nDone! {self.page_no()} pages generated.")
        print(f"Output: {output_path}")
        size_kb = os.path.getsize(output_path) / 1024
        print(f"Size: {size_kb:.1f} KB")


if __name__ == "__main__":
    output = os.path.join(os.path.dirname(__file__), "BreakoutScan_Design_System.pdf")
    pdf = DesignSystemPDF()
    pdf.generate(output)
