#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Falcon-style Mission Briefing -> A4 Portrait Kneeboard PDF

Input:
    briefing.txt

Output:
    briefing.pdf

Dependency:
    pip install reportlab
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    PageTemplate,
    Frame,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
)
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics


# ============================================================
# CONFIG
# ============================================================

PAGE_WIDTH, PAGE_HEIGHT = A4

# LEFT = 11 * mm
# RIGHT = 11 * mm
# TOP = 15 * mm
# BOTTOM = 13 * mm

LEFT = 5 * mm
RIGHT = 5 * mm
TOP = 5 * mm
BOTTOM = 5 * mm

CONTENT_WIDTH = PAGE_WIDTH - LEFT - RIGHT
TABLE_INSET = 3 * mm
TABLE_WIDTH = CONTENT_WIDTH - 2 * TABLE_INSET

INPUT_DEFAULT = "briefing.txt"
OUTPUT_DEFAULT = "briefing.pdf"


# ============================================================
# COLORS
# ============================================================

NAVY = colors.HexColor("#17324D")
BLUE = colors.HexColor("#235B82")
LIGHT_BLUE = colors.HexColor("#E8F1F7")
VERY_LIGHT_BLUE = colors.HexColor("#F5F9FC")

DARK = colors.HexColor("#202A33")
GREY = colors.HexColor("#64727E")
LIGHT_GREY = colors.HexColor("#D7DEE4")

GREEN = colors.HexColor("#2F6B45")
LIGHT_GREEN = colors.HexColor("#EDF7F0")

RED = colors.HexColor("#9E2A2B")
LIGHT_RED = colors.HexColor("#FFF0F0")

AMBER = colors.HexColor("#8A5A00")
LIGHT_AMBER = colors.HexColor("#FFF7E3")

WHITE = colors.white

POSSIBLE_SECTIONS = [
    "Mission Overview:",
    "Situation:",
    "Pilot Roster:",
    "Package Elements:",
    "Threat Analysis:",
    "Steerpoints:",
    "Comm Ladder:",
    "Iff",
    "Link 16",
    "Ordnance:",
    "Weather:",
    "Support:",
    "Rules of Engagement:",
    "Emergency Procedures:",
    "END_OF_BRIEFING",
]

sections = []

# ============================================================
# FONTS
# ============================================================

def setup_fonts():
    candidates = [
        (
            "DejaVuSans",
            "DejaVuSans-Bold",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ),
        (
            "DejaVuSans",
            "DejaVuSans-Bold",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ),
        (
            "DejaVuSans",
            "DejaVuSans-Bold",
            "C:/Windows/Fonts/DejaVuSans.ttf",
            "C:/Windows/Fonts/DejaVuSans-Bold.ttf",
        ),
    ]

    for regular_name, bold_name, regular, bold in candidates:
        if Path(regular).exists() and Path(bold).exists():
            pdfmetrics.registerFont(TTFont(regular_name, regular))
            pdfmetrics.registerFont(TTFont(bold_name, bold))
            return regular_name, bold_name

    return "Helvetica", "Helvetica-Bold"


FONT, FONT_BOLD = setup_fonts()


# ============================================================
# STYLES
# ============================================================

base = getSampleStyleSheet()

TITLE = ParagraphStyle(
    "Title",
    fontName=FONT_BOLD,
    fontSize=20,
    leading=23,
    alignment=TA_CENTER,
    textColor=NAVY,
    spaceAfter=2 * mm,
)

SUBTITLE = ParagraphStyle(
    "Subtitle",
    fontName=FONT,
    fontSize=8.5,
    leading=11,
    alignment=TA_CENTER,
    textColor=GREY,
)

SECTION = ParagraphStyle(
    "Section",
    fontName=FONT_BOLD,
    fontSize=10.5,
    leading=12,
    textColor=WHITE,
    spaceBefore=2 * mm,
    spaceAfter=2 * mm,
)

SUBSECTION = ParagraphStyle(
    "Subsection",
    fontName=FONT_BOLD,
    fontSize=8.5,
    leading=10,
    textColor=NAVY,
    spaceBefore=1.5 * mm,
    spaceAfter=1 * mm,
)

BODY = ParagraphStyle(
    "Body",
    fontName=FONT,
    fontSize=8.0,
    leading=10.5,
    textColor=DARK,
)

BODY_SMALL = ParagraphStyle(
    "BodySmall",
    fontName=FONT,
    fontSize=7.0,
    leading=8.5,
    textColor=DARK,
)

BODY_BOLD = ParagraphStyle(
    "BodyBold",
    fontName=FONT_BOLD,
    fontSize=8.0,
    leading=10,
    textColor=DARK,
)

CARD_TITLE = ParagraphStyle(
    "CardTitle",
    fontName=FONT_BOLD,
    fontSize=8.5,
    leading=10,
    textColor=WHITE,
)

LABEL = ParagraphStyle(
    "Label",
    fontName=FONT_BOLD,
    fontSize=6.5,
    leading=7.5,
    textColor=GREY,
)

VALUE = ParagraphStyle(
    "Value",
    fontName=FONT_BOLD,
    fontSize=9,
    leading=10,
    textColor=NAVY,
)

MONO = ParagraphStyle(
    "Mono",
    fontName="Courier",
    fontSize=6.5,
    leading=8,
    textColor=DARK,
)

MONO_SMALL = ParagraphStyle(
    "MonoSmall",
    # fontName="Courier",
    fontName=FONT_BOLD,
    # fontSize=5.8,
    fontSize=6.5,
    leading=7,
    textColor=DARK,
)

CALLOUT = ParagraphStyle(
    "Callout",
    fontName=FONT_BOLD,
    fontSize=8.2,
    leading=10.5,
    textColor=RED,
)


# ============================================================
# BASIC HELPERS
# ============================================================

def esc(value: str) -> str:
    """Escape basic XML entities for ReportLab Paragraph."""
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


# def P(value: str, style=BODY) -> Paragraph:
#     return Paragraph(esc(value), style)


def P(value: str, style=BODY) -> Paragraph:
    """
    Normaler Text.
    HTML/XML-Sonderzeichen werden escaped.
    """
    return Paragraph(esc(value), style)


def PH(value: str, style=BODY) -> Paragraph:
    """
    ReportLab-Markup erlauben.
    Beispiel:
        PH("<b>ACTION:</b> Climb immediate")
    """
    return Paragraph(value, style)


def clean(value: str) -> str:
    value = value.replace("\xa0", " ")
    value = value.strip()
    value = re.sub(r"[ \t]+", " ", value)
    return value


def cols(line: str) -> List[str]:
    """
    Splits the original briefing's pseudo-table format.
    The source uses tabs and/or multiple spaces as delimiters.
    """
    line = line.replace("\t", "    ").strip()

    if not line:
        return []

    return [
        x.strip()
        for x in re.split(r"\s{2,}", line)
        if x.strip()
    ]


def extract_after(label: str, text: str) -> str:
    match = re.search(
        rf"{re.escape(label)}\s*:?\s*(.+)",
        text,
        re.IGNORECASE,
    )
    return match.group(1).strip() if match else ""


def get_section(lines: List[str], name: str) -> List[str]:
    """
    Extracts everything between 'name' and the next known section.
    """

    # sections = [
    #     "Mission Overview:",
    #     "Situation:",
    #     "Pilot Roster:",
    #     "Package Elements: \tx  = Primary Flight",
    #     "Threat Analysis:",
    #     "Steerpoints:",
    #     "Comm Ladder:",
    #     "Iff",
    #     "Link 16",
    #     "Ordnance:",
    #     "Weather:",
    #     "Support:",
    #     "Rules of Engagement:",
    #     "Emergency Procedures:",
    #     "END_OF_BRIEFING",
    # ]

    start = None

    for i, line in enumerate(lines):
        if line.strip().lower() == name.strip().lower():
            start = i + 1
            break

    if start is None:
        return []

    result = []

    for line in lines[start:]:
        stripped = line.strip()

        if any(stripped.lower() == s.lower() for s in sections):
            break

        # if any(
        #     stripped.lower().startswith(s.lower())
        #     for s in sections
        # ):
        #     break

        result.append(line)

    return result


def first_nonempty(lines: List[str]) -> str:
    for line in lines:
        if line.strip():
            return line.strip()
    return ""


# ============================================================
# CARD BUILDERS
# ============================================================

def section_header(title: str):
    t = Table(
        [[P(title, SECTION)]],
        colWidths=[CONTENT_WIDTH],
    )

    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("BOX", (0, 0), (-1, -1), 0.4, NAVY),
    ]))

    return t


def small_header(title: str):
    return Table(
        [[P(title.upper(), CARD_TITLE)]],
        colWidths=[CONTENT_WIDTH],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), BLUE),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]),
    )


def key_value_table(items: List[Tuple[str, str]], widths=None):
    if widths is None:
        widths = [39 * mm, CONTENT_WIDTH - 39 * mm]

    data = []

    for key, value in items:
        data.append([
            P(key.upper(), LABEL),
            P(value, BODY_BOLD),
        ])

    table = Table(
        data,
        # colWidths=widths,
        # hAlign="CENTER",
        colWidths=widths,
        hAlign="LEFT",
    )

    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -2), 0.3, LIGHT_GREY),
        ("LINEAFTER", (0, 0), (0, -1), 0.3, LIGHT_GREY),
        # ("GRID", (0, 0), (-1, -1), 0.3, LIGHT_GREY),
        ("BACKGROUND", (0, 0), (0, -1), VERY_LIGHT_BLUE),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))

    return table


def card(title: str, body, background=VERY_LIGHT_BLUE):
    if isinstance(body, list):
        flow = body
    else:
        flow = [body]

    rows = [
        [P(title.upper(), CARD_TITLE)],
    ]

    for item in flow:
        rows.append([item])

    table = Table(
        rows,
        colWidths=[CONTENT_WIDTH],
        # colWidths=[CONTENT_WIDTH - 2 * TABLE_INSET],
        # hAlign="CENTER",
    )

    style = [
        ("BACKGROUND", (0, 0), (-1, 0), BLUE),
        ("BACKGROUND", (0, 1), (-1, -1), background),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("BOX", (0, 0), (-1, -1), 0.45, LIGHT_GREY),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]

    table.setStyle(TableStyle(style))

    return table


def two_column_cards(left, right, gap=4 * mm):
    width = (CONTENT_WIDTH - gap) / 2

    table = Table(
        [[left, right]],
        colWidths=[width, width],
    )

    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (0, 0), gap / 2),
        ("LEFTPADDING", (1, 0), (1, 0), gap / 2),
        ("RIGHTPADDING", (1, 0), (1, 0), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    return table


# ============================================================
# HEADER / FOOTER
# ============================================================

class BriefingDocTemplate(BaseDocTemplate):

    def __init__(self, filename, **kwargs):
        super().__init__(filename, **kwargs)

        frame = Frame(
            LEFT,
            BOTTOM,
            CONTENT_WIDTH,
            PAGE_HEIGHT - TOP - BOTTOM,
            id="normal",
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0,
        )

        self.addPageTemplates([
            PageTemplate(
                id="portrait",
                frames=frame,
                onPage=self.draw_page,
            )
        ])

    def draw_page(self, canvas, doc):
        canvas.saveState()

        # Header
        canvas.setStrokeColor(NAVY)
        canvas.setLineWidth(0.7)

        canvas.line(
            LEFT,
            PAGE_HEIGHT - 9 * mm,
            PAGE_WIDTH - RIGHT,
            PAGE_HEIGHT - 9 * mm,
        )

        canvas.setFont(FONT_BOLD, 6.5)
        canvas.setFillColor(GREY)

        canvas.drawString(
            LEFT,
            PAGE_HEIGHT - 6.5 * mm,
            "MISSION BRIEFING",
        )

        canvas.drawRightString(
            PAGE_WIDTH - RIGHT,
            PAGE_HEIGHT - 6.5 * mm,
            "KNEEBOARD",
        )

        # Footer
        canvas.line(
            LEFT,
            8 * mm,
            PAGE_WIDTH - RIGHT,
            8 * mm,
        )

        canvas.setFont(FONT, 6.5)
        canvas.setFillColor(GREY)

        canvas.drawString(
            LEFT,
            5 * mm,
            "TACTICAL BRIEFING RECORD",
        )

        canvas.drawRightString(
            PAGE_WIDTH - RIGHT,
            5 * mm,
            f"PAGE {doc.page}",
        )

        canvas.restoreState()


# ============================================================
# PARSING MISSION HEADER
# ============================================================

def parse_header(overview: str):
    result = []

    # print(overview)
    first = True
    for line in overview:
        if line.strip() == "":
            continue
        else:
            line.strip()
            if first:
                clean = line.strip()
                callsign_type = clean.split(" ")
                result.append(callsign_type[0])
                result.append(callsign_type[1])
                first = False
            else:
                clean = line.strip()
                key_value = clean.split(":", 1)
                key_value[1] = key_value[1].strip()
                result.append(key_value)
    # print(result)
    return result


# ============================================================
# PAGE 1 — MISSION OVERVIEW
# ============================================================DDER

def render_mission_page(story, raw, lines):

    m = re.search(
        r"BRIEFING RECORD generated at (.+?)[\n]*",
        raw
    )
    generated = clean(m.group(1))

    # Titel und Overview
    overview = get_section(lines, "Mission Overview:")
    key_values = parse_header(overview)

    story.append(Spacer(1, 10 * mm))

    story.append(P("MISSION BRIEFING", TITLE))

    subtitle = (
        f"{key_values[0]}  •  "
        f"{key_values[1]}  •  "
        f"PACKAGE {key_values[2][1]}"
    )

    story.append(P(subtitle, SUBTITLE))
    story.append(Spacer(1, 4 * mm))

    rendered = []
    for kv in key_values[2:]:
        if kv:
            rendered.append(
                key_value_table([
                    (kv[0], kv[1]),
                ])
            )

    story.append(
        card(
            "MISSION QUICK REFERENCE",
            rendered,
        )
    )

    story.append(Spacer(1, 3 * mm))

    # Situation
    situation = get_section(lines, "Situation:")

    paragraphs = []

    for line in situation:
        text = clean(line)

        if not text:
            continue

        if text.lower().startswith("potential targets"):
            paragraphs.append(
                P(text, BODY_BOLD)
            )
        else:
            paragraphs.append(
                P(text, BODY)
            )

    if paragraphs:
        story.append(card("SITUATION", paragraphs))
        story.append(Spacer(1, 3 * mm))

    # Pilot roster
    roster = get_section(lines, "Pilot Roster:")

    roster_rows = []

    for line in roster:
        c = cols(line)
        if len(c) >= 2:
            roster_rows.append(c)

    if roster_rows:
        table_data = []

        for i, row in enumerate(roster_rows):
            table_data.append([
                P(x, BODY_SMALL if i else BODY_BOLD)
                for x in row
            ])

        # Normalize to 5 columns
        max_cols = min(5, max(len(r) for r in roster_rows))

        normalized = []
        for row in roster_rows:
            normalized.append(
                row[:max_cols] + [""] * max(0, max_cols - len(row))
            )

        table = Table(
            [
                [P(x, BODY_BOLD) for x in row]
                for row in normalized
            ],
            colWidths=[(CONTENT_WIDTH) / max_cols] * max_cols,
        )

        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), LIGHT_BLUE),
            # ("LINEBELOW", (0, 0), (-1, -2), 0.3, LIGHT_GREY),
            # ("LINEAFTER", (0, 0), (0, -1), 0.3, LIGHT_GREY),
            ("GRID", (0, 0), (-1, -1), 0.3, LIGHT_GREY),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))

        story.append(card("PILOT ROSTER", []))
        story.append(table)
        story.append(Spacer(1, 3 * mm))

    # Package elements
    package = get_section(lines, "Package Elements: \tx  = Primary Flight")

    package_rows = []

    for line in package:
        c = cols(line)

        if len(c) >= 3:
            package_rows.append(c)

    if package_rows:
        data = []

        # for row in package_rows:
        #     data.append([
        #         P(x, BODY_BOLD)
        #         for x in row
        #     ])

        for i, row in enumerate(package_rows):
            data.append([
                P(x, BODY_SMALL if i else BODY_BOLD)
                for x in row
            ])

        table = Table(
            data,
            colWidths=None,
        )

        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), LIGHT_BLUE),
            ("GRID", (0, 0), (-1, -1), 0.3, LIGHT_GREY),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))

        story.append(card("PACKAGE / FLIGHT", []))
        story.append(table)

# ============================================================
# PAGE 2 — STEERPOINTS
# ============================================================

def parse_steerpoints(lines):
    result = []

    for line in lines:
        c = cols(line)

        if not c:
            continue

        if c[0].isdigit():
            # Source format:
            # # Desc Time Dist Head Cas Alt Action Form Comments

            row = {
                "number": c[0],
                "desc": c[1] if len(c) > 1 else "",
                "time": c[2] if len(c) > 2 else "",
                "dist": c[3] if len(c) > 3 else "",
                "head": c[4] if len(c) > 4 else "",
                "cas": c[5] if len(c) > 5 else "",
                "alt": c[6] if len(c) > 6 else "",
                "action": c[7] if len(c) > 7 else "",
                "form": c[8] if len(c) > 8 else "",
                "comments": " ".join(c[9:]) if len(c) > 9 else "",
            }

            result.append(row)

    return result


def render_steerpoints_page(story, lines):

    points = parse_steerpoints(
        get_section(lines, "Steerpoints:")
    )

    if not points:
        return

    story.append(section_header("STEERPOINTS"))
    story.append(Spacer(1, 2 * mm))

    for sp in points:

        number = sp["number"]
        desc = sp["desc"] or "—"

        title = f"{number}  {desc.upper()}"

        left = [
            [P("TIME", LABEL), P(sp["time"] or "—", VALUE)],
            [P("DIST", LABEL), P(sp["dist"] or "—", BODY_BOLD)],
            [P("HEADING", LABEL), P(sp["head"] or "—", BODY_BOLD)],
        ]

        right = [
            [P("CAS", LABEL), P(sp["cas"] or "—", BODY_BOLD)],
            [P("ALT", LABEL), P(sp["alt"] or "—", BODY_BOLD)],
            [P("FORM", LABEL), P(sp["form"] or "—", BODY_BOLD)],
        ]

        def mini(data):
            t = Table(
                data,
                colWidths=[18 * mm, 30 * mm],
            )
            t.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 1),
                ("RIGHTPADDING", (0, 0), (-1, -1), 1),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ]))
            return t

        body = [
            two_column_cards(
                mini(left),
                mini(right),
            )
        ]

        if sp["action"]:
            body.append(
                PH(
                    f"<b>ACTION:</b> {esc(sp['action'])}",
                    BODY,
                )
            )

        if sp["comments"]:
            body.append(
                PH(
                    f"<b>NOTE:</b> {esc(sp['comments'])}",
                    BODY,
                )
            )

        background = (
            LIGHT_GREEN
            if sp["desc"].upper() == "CAP"
            else VERY_LIGHT_BLUE
        )

        story.append(
            card(
                title,
                body,
                background=background,
            )
        )

        story.append(Spacer(1, 2 * mm))


# ============================================================
# PAGE 3 — COMM LADDER
# ============================================================

def render_comm_page(story, lines):

    raw = get_section(lines, "Comm Ladder:")

    if not raw:
        return

    story.append(section_header("COMM LADDER"))
    story.append(Spacer(1, 2 * mm))

    categories = {
        "INTRA-FLIGHT": [],
        "AWACS": [],
        "TANKER / AAR": [],
        "DEPARTURE": [],
        "ARRIVAL": [],
        "COMMON / GUARD": [],
        "ALTERNATE": [],
        "OTHER": [],
    }

    for line in raw:
        c = cols(line)

        if len(c) < 2:
            continue

        if c[0] == "Intra-Flight:":
            category = "INTRA-FLIGHT"
        elif c[0] == "Tactical:" or c[0] == "Check-In:":
            category = "AWACS"
        elif c[0] == "Tanker / Aar:":
            category = "TANKER / AAR"
        elif c[0] in ["Dep Atis:", "Dep Ground:", "Dep Tower:", "Dep Departure:"]:
            category = "DEPARTURE"
        elif c[0] in ["Arr Atis:", "Arr Approach:", "Arr Tower:", "Arr Ground:"]:
            category = "ARRIVAL"
        elif c[0] in ["Alt Atis:", "Alt Approach:", "Alt Tower:", "Alt Ground:"]:
            category = "ALTERNATE"
        elif c[0] in ["Guard:", "Common:", "Base Ops:"]:
            category = "COMMON / GUARD"
        else:
            category = "OTHER"

        # text = " ".join(c).lower()

        # if "intra-flight" in text:
        #     category = "INTRA-FLIGHT"
        # elif "tactical" in text:
        #     category = "AWACS"
        # elif "tanker" in text:
        #     category = "TANKER / AAR"
        # elif "dep " in text or "departure" in text:
        #     category = "DEPARTURE"
        # elif "arr " in text or "recovery" in text:
        #     category = "ARRIVAL"
        # elif "alt " in text or "alternate" in text:
        #     category = "ALTERNATE"
        # elif "guard" in text or "common" in text:
        #     category = "COMMON / GUARD"
        # else:
        #     category = "OTHER"

        # print(category)
        categories[category].append(c)

    for category, rows in categories.items():

        if not rows or category == "OTHER":
            continue

        if category == "DEPARTURE" or category == "COMMON / GUARD":
            story.append(PageBreak())

        rendered = []

        for row in rows:

            agency = row[0] if len(row) > 0 else ""
            callsign = row[1] if len(row) > 1 else ""
            uhf = row[2] if len(row) > 2 else ""
            vhf = row[3] if len(row) > 3 else ""
            notes = " ".join(row[4:]) if len(row) > 4 else ""

            rendered.append(
                key_value_table([
                    ("AGENCY", agency),
                    ("CALLSIGN", callsign),
                    ("UHF", uhf),
                    ("VHF", vhf),
                    ("NOTE", notes),
                ])
            )

        story.append(
            card(
                category,
                rendered,
                background=VERY_LIGHT_BLUE,
            )
        )

        story.append(Spacer(1, 2 * mm))


# ============================================================
# PAGE 4 — IFF
# ============================================================

def render_iff_page(story, lines):

    raw = get_section(lines, "Iff")

    if not raw:
        return

    story.append(section_header("IFF"))
    story.append(Spacer(1, 2 * mm))

    general = []
    time_events = []
    pos_events = []

    mode = "general"

    for line in raw:

        text = clean(line)

        if not text:
            continue

        upper = text.upper()

        if upper == "GENERAL:":
            mode = "general"
            continue

        if upper == "TIME EVENTS:":
            mode = "time"
            continue

        if upper == "POS EVENTS:":
            mode = "pos"
            continue

        c = cols(line)

        if mode == "general":
            if c:
                general.append(c)

        elif mode == "time":
            if c:
                time_events.append(c)

        elif mode == "pos":
            if c:
                pos_events.append(c)

    # General
    if general:
        rendered = []

        for row in general:
            if len(row) >= 2:
                rendered.append(
                    key_value_table([
                        (row[0], " ".join(row[1:])),
                    ])
                )

        story.append(
            card(
                "GENERAL",
                rendered,
            )
        )

        story.append(Spacer(1, 2 * mm))

    # Time events
    if time_events:

        story.append(
            card(
                "TIME EVENTS",
                [],
            )
        )

        # Rebuild as a compact table
        data = []

        for row in time_events:
            data.append([
                P(x, MONO_SMALL)
                for x in row
            ])

        if data:

            # Force to manageable width
            n = max(len(x) for x in data)

            table = Table(
                data,
                colWidths=[CONTENT_WIDTH / n] * n,
            )

            table.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.3, LIGHT_GREY),
                ("BACKGROUND", (0, 0), (-1, 0), LIGHT_BLUE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]))

            story.append(table)

        story.append(Spacer(1, 2 * mm))

    # Position events
    if pos_events:

        rendered = []

        for row in pos_events:
            if len(row) >= 2:
                rendered.append(
                    key_value_table([
                        (row[0], " ".join(row[1:])),
                    ])
                )

        story.append(
            card(
                "POSITION EVENTS",
                rendered,
            )
        )


# ============================================================
# PAGE 4 — LINK 16 changed
# ============================================================

def render_link16_page(story, lines):

    raw = get_section(lines, "Link 16")

    if not raw:
        return

    story.append(section_header("LINK 16"))
    story.append(Spacer(1, 2 * mm))

    file_a = []
    file_b = []
    pos_events = []

    mode = "file_a"

    for line in raw:

        text = clean(line)

        if not text:
            continue

        upper = text.upper()

        if upper == "FILE A:":
            mode = "file_a"
            continue

        if upper == "FILE B:":
            mode = "file_b"
            continue

        c = cols(line)

        if mode == "file_a":
            if c:
                file_a.append(c)

        elif mode == "file_b":
            if c:
                file_b.append(c)

    # File A
    if file_a:
        rendered = []

        data = []

        for row in file_a:

            if len(row) <= 4:
                for item in row:
                    links, rechts = item.split(":", 1)
                    links += ":"
                    rechts = rechts.strip()
                    rendered.append(
                        key_value_table([
                            (links, rechts),
                        ])
                    )
            else:
                row = row[:9] + [" ".join(row[9:])]
                # print(row)
                data.append([
                    P(x, MONO_SMALL)
                    for x in row
                ])

        story.append(
            card(
                "FILE A",
                rendered,
            )
        )

        if data:

            # Force to manageable width
            # n = max(len(x) for x in data)

            n = len(data[0])

            normal_width = CONTENT_WIDTH * 0.08
            last_width = CONTENT_WIDTH * 0.28

            col_widths = [normal_width] * 9 + [last_width]

            table = Table(
                data,
                colWidths=col_widths,
            )

            table.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.3, LIGHT_GREY),
                ("BACKGROUND", (0, 0), (-1, 0), LIGHT_BLUE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]))

            story.append(table)

        story.append(Spacer(1, 2 * mm))

    # File B
    if file_b:
        rendered = []

        data = []

        for row in file_b:

            if len(row) <= 4:
                for item in row:
                    links, rechts = item.split(":", 1)
                    links += ":"
                    rechts = rechts.strip()
                    rendered.append(
                        key_value_table([
                            (links, rechts),
                        ])
                    )
            else:
                row = row[:9] + [" ".join(row[9:])]
                # print(row)
                data.append([
                    P(x, MONO_SMALL)
                    for x in row
                ])

        story.append(
            card(
                "FILE B",
                rendered,
            )
        )

        if data:

            # Force to manageable width
            # n = max(len(x) for x in data)

            n = len(data[0])

            normal_width = CONTENT_WIDTH * 0.08
            last_width = CONTENT_WIDTH * 0.28

            col_widths = [normal_width] * 9 + [last_width]

            table = Table(
                data,
                colWidths=col_widths,
            )

            table.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.3, LIGHT_GREY),
                ("BACKGROUND", (0, 0), (-1, 0), LIGHT_BLUE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]))

            story.append(table)

        story.append(Spacer(1, 2 * mm))

# ============================================================
# PAGE 5 — LINK 16
# ============================================================

def render_link16_page_old(story, lines):

    raw = get_section(lines, "Link 16")

    if not raw:
        return

    story.append(section_header("LINK 16"))
    story.append(Spacer(1, 2 * mm))

    current_file = None
    current_lines = []

    files = []

    for line in raw:

        text = clean(line)

        if not text:
            continue

        m = re.match(r"(FILE\s+[AB]):?", text, re.IGNORECASE)

        if m:

            if current_file:
                files.append(
                    (current_file, current_lines)
                )

            current_file = m.group(1).upper()
            current_lines = []

        else:
            current_lines.append(line)

    if current_file:
        files.append(
            (current_file, current_lines)
        )

    for filename, file_lines in files:

        story.append(
            small_header(filename)
        )

        items = []

        for line in file_lines:

            c = cols(line)

            if not c:
                continue

            if ":" in c[0]:
                key = c[0].rstrip(":")
                value = " ".join(c[1:])

                items.append(
                    (key, value)
                )

        if items:
            story.append(
                key_value_table(items)
            )

        # Raw STNS / channels block
        for line in file_lines:

            text = line.strip()

            if (
                text.startswith("STNS") or text.startswith("Donor") or text.startswith("Team") or text.startswith("Flight")
            ):
                story.append(
                    Spacer(1, 1 * mm)
                )

                story.append(
                    P(
                        text,
                        MONO,
                    )
                )

        story.append(Spacer(1, 3 * mm))


# ============================================================
# PAGE 6 — ORDNANCE / WEATHER
# ============================================================

def render_ordnance_page(story, lines):

    raw = get_section(lines, "Ordnance:")

    if not raw:
        return

    story.append(section_header("ORDNANCE"))
    story.append(Spacer(1, 2 * mm))

    # We preserve the original loadout lines but make them readable.
    for line in raw:

        text = clean(line)

        if not text:
            continue

        if "Callsign:" in text:
            continue

        if text.startswith("Gamble2"):
            continue

        # Detect actual weapon lines
        if re.match(
            r"^\d+x?\s+",
            text,
            re.IGNORECASE,
        ):
            story.append(
                Table(
                    [[
                        P("LOAD", LABEL),
                        P(text, BODY_BOLD),
                    ]],
                    colWidths=[
                        20 * mm,
                        CONTENT_WIDTH - 20 * mm,
                    ],
                    style=TableStyle([
                        ("BACKGROUND", (0, 0), (0, 0), LIGHT_BLUE),
                        ("BOX", (0, 0), (-1, -1), 0.3, LIGHT_GREY),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 4),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ]),
                )
            )

            story.append(Spacer(1, 1 * mm))

        else:
            story.append(
                P(text, BODY)
            )


def render_weather_page(story, lines):

    raw = get_section(lines, "Weather:")

    if not raw:
        return

    story.append(section_header("WEATHER"))
    story.append(Spacer(1, 2 * mm))

    rows = []

    for line in raw:

        c = cols(line)

        if len(c) >= 2:
            rows.append(c)

    if rows:

        max_cols = max(len(r) for r in rows)

        normalized = [
            r[:max_cols] + [""] * max(0, max_cols - len(r))
            for r in rows
        ]

        table = Table(
            [
                [P(x, BODY_SMALL) for x in row]
                for row in normalized
            ],
            colWidths=[CONTENT_WIDTH / max_cols] * max_cols,
        )

        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), LIGHT_BLUE),
            ("GRID", (0, 0), (-1, -1), 0.3, LIGHT_GREY),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))

        story.append(table)


# ============================================================
# PAGE 7 — SUPPORT / THREATS / ROE
# ============================================================

def render_support_threats_page(story, lines):

    # Threats
    threat = get_section(lines, "Threat Analysis:")

    if threat:

        story.append(section_header("THREAT ANALYSIS"))
        story.append(Spacer(1, 2 * mm))

        air = []
        sam = []

        mode = None

        for line in threat:

            text = clean(line)

            if not text:
                continue

            lower = text.lower()

            if lower.startswith("air-to-air"):
                mode = "air"
                continue

            if lower.startswith("surface-to-air"):
                mode = "sam"
                continue

            if mode == "air":
                air.append(text)

            elif mode == "sam":
                sam.append(text)

        if air:
            story.append(
                card(
                    "AIR-TO-AIR THREATS",
                    [P(x, BODY) for x in air],
                    background=LIGHT_RED,
                )
            )

            story.append(Spacer(1, 2 * mm))

        if sam:
            story.append(
                card(
                    "SURFACE-TO-AIR THREATS",
                    [P(x, BODY) for x in sam],
                    background=LIGHT_GREEN,
                )
            )

            story.append(Spacer(1, 3 * mm))

    # Support
    support = get_section(lines, "Support:")

    if support:

        story.append(section_header("SUPPORT"))

        paragraphs = [
            P(clean(x), BODY)
            for x in support
            if clean(x)
        ]

        story.append(
            card(
                "SUPPORT ASSETS",
                paragraphs,
            )
        )

        story.append(Spacer(1, 3 * mm))

    # ROE
    roe = get_section(lines, "Rules of Engagement:")

    if roe:

        story.append(section_header("RULES OF ENGAGEMENT"))

        paragraphs = [
            P(clean(x), CALLOUT)
            for x in roe
            if clean(x)
        ]

        story.append(
            card(
                "ROE",
                paragraphs,
                background=LIGHT_AMBER,
            )
        )


# ============================================================
# PAGE 8 — EMERGENCY
# ============================================================

def render_emergency_page(story, lines):

    raw = get_section(
        lines,
        "Emergency Procedures:",
    )

    if not raw:
        return

    story.append(
        section_header(
            "EMERGENCY PROCEDURES"
        )
    )

    current_title = None
    current_body = []

    def flush():

        nonlocal current_title, current_body

        if current_title:

            story.append(
                card(
                    current_title,
                    [
                        P(x, BODY)
                        for x in current_body
                        if clean(x)
                    ],
                    background=LIGHT_RED
                    if "DISTRESS" in current_title.upper()
                    else VERY_LIGHT_BLUE,
                )
            )

            story.append(
                Spacer(1, 2 * mm)
            )

        current_title = None
        current_body = []

    for line in raw:

        text = clean(line)

        if not text:
            continue

        # Known emergency subheadings
        if (
            text.endswith(":") or text.lower().startswith("alternate airfield")
        ):

            flush()

            current_title = text.rstrip(":")

        else:
            current_body.append(text)

    flush()

    # Closing note
    story.append(
        Spacer(1, 4 * mm)
    )

    story.append(
        Table(
            [[
                P(
                    "GOOD LUCK!",
                    ParagraphStyle(
                        "GoodLuck",
                        fontName=FONT_BOLD,
                        fontSize=12,
                        leading=14,
                        alignment=TA_CENTER,
                        textColor=WHITE,
                    ),
                )
            ]],
            colWidths=[CONTENT_WIDTH],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), NAVY),
                ("BOX", (0, 0), (-1, -1), 0.5, NAVY),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]),
        )
    )


# ============================================================
# BUILD DOCUMENT
# ============================================================

def build_pdf(input_file: str, output_file: str):

    path = Path(input_file)

    if not path.exists():
        raise FileNotFoundError(
            f"Datei nicht gefunden: {input_file}"
        )

    raw = path.read_text(
        encoding="utf-8",
        errors="replace",
    )

    lines = raw.splitlines()

    for line in lines:
        section = line[:line.find(":") + 1] if ":" in line else line
        if section in POSSIBLE_SECTIONS:
            sections.append(line.strip())
    # print(sections)

    doc = BriefingDocTemplate(
        output_file,
        pagesize=A4,
        leftMargin=LEFT,
        rightMargin=RIGHT,
        topMargin=TOP,
        bottomMargin=BOTTOM,
        title="Mission Briefing",
        author="Kneeboard Briefing Generator",
        subject="Mission Briefing",
    )

    story = []

    # --------------------------------------------------------
    # PAGE 1
    # --------------------------------------------------------

    render_mission_page(
        story,
        raw,
        lines,
    )

    story.append(PageBreak())

    # --------------------------------------------------------
    # PAGE 2
    # --------------------------------------------------------

    render_steerpoints_page(
        story,
        lines,
    )

    story.append(PageBreak())

    # --------------------------------------------------------
    # PAGE 3
    # --------------------------------------------------------

    render_comm_page(
        story,
        lines,
    )

    story.append(PageBreak())

    # --------------------------------------------------------
    # PAGE 4
    # --------------------------------------------------------

    render_iff_page(
        story,
        lines,
    )

    story.append(PageBreak())

    # --------------------------------------------------------
    # PAGE 5
    # --------------------------------------------------------

    render_link16_page(
        story,
        lines,
    )

    story.append(PageBreak())

    # --------------------------------------------------------
    # PAGE 6
    # --------------------------------------------------------

    render_ordnance_page(
        story,
        lines,
    )

    story.append(Spacer(1, 4 * mm))

    render_weather_page(
        story,
        lines,
    )

    story.append(PageBreak())

    # --------------------------------------------------------
    # PAGE 7
    # --------------------------------------------------------

    render_support_threats_page(
        story,
        lines,
    )

    story.append(PageBreak())

    # --------------------------------------------------------
    # PAGE 8
    # --------------------------------------------------------

    render_emergency_page(
        story,
        lines,
    )

    # --------------------------------------------------------
    # BUILD
    # --------------------------------------------------------

    doc.build(story)

    print()
    print("=" * 60)
    print("PDF erfolgreich erstellt")
    print("=" * 60)
    print(f"Eingabe : {input_file}")
    print(f"Ausgabe : {output_file}")
    print("=" * 60)


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":

    input_file = (
        sys.argv[1]
        if len(sys.argv) > 1
        else INPUT_DEFAULT
    )

    output_file = (
        sys.argv[2]
        if len(sys.argv) > 2
        else OUTPUT_DEFAULT
    )

    # build_pdf(input_file, output_file)

    try:
        build_pdf(
            input_file,
            output_file,
        )

    except Exception as exc:

        print()
        print("FEHLER:")
        print(exc)
        print()

        sys.exit(1)
