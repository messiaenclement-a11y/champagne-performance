from __future__ import annotations

from io import BytesIO
from pathlib import Path
from urllib.request import Request, urlopen

from PIL import Image as PILImage, ImageDraw
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from services.report_charts import progression_chart, radar_comparison_chart
from services.report_stats import CONTEXTS, ZONES
from utils.formatting import player_label, seconds_to_hms

PAGE_W, PAGE_H = A4
DARK = colors.HexColor("#1A2434")
LIGHT = colors.HexColor("#04B3EA")
GOLD = colors.HexColor("#B8A05A")
WHITE = colors.white
PALE = colors.HexColor("#F3F7FA")
CARD = colors.HexColor("#F2F3F5")
TEXT = colors.HexColor("#334155")
MUTED = colors.HexColor("#6B7280")
LINE = colors.HexColor("#E5E7EB")
GREEN = colors.HexColor("#2E9D68")
ORANGE = colors.HexColor("#E69232")
RED = colors.HexColor("#D85252")

MONTH_NAMES = [
    "", "JANVIER", "FÉVRIER", "MARS", "AVRIL", "MAI", "JUIN",
    "JUILLET", "AOÛT", "SEPTEMBRE", "OCTOBRE", "NOVEMBRE", "DÉCEMBRE",
]

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOGO_PATH = PROJECT_ROOT / "assets" / "logo_champagne_basket.png"


def _download_image(url: str | None) -> bytes | None:
    if not url:
        return None
    try:
        request = Request(url, headers={"User-Agent": "ChampagnePerformance/1.0"})
        with urlopen(request, timeout=5) as response:
            return response.read()
    except Exception:
        return None


def _placeholder_photo(width: int = 360, height: int = 480) -> bytes:
    image = PILImage.new("RGB", (width, height), "#E8EEF3")
    draw = ImageDraw.Draw(image)
    draw.ellipse((width * .31, height * .13, width * .69, height * .42), fill="#C7D5DF")
    draw.rounded_rectangle((width * .18, height * .42, width * .82, height * .92), radius=55, fill="#C7D5DF")
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def _fit_photo_rect(raw: bytes, width: int = 360, height: int = 480) -> bytes:
    try:
        image = PILImage.open(BytesIO(raw)).convert("RGB")
        source_ratio = image.width / image.height
        target_ratio = width / height
        if source_ratio > target_ratio:
            new_width = int(image.height * target_ratio)
            left = (image.width - new_width) // 2
            image = image.crop((left, 0, left + new_width, image.height))
        else:
            new_height = int(image.width / target_ratio)
            top = max(0, (image.height - new_height) // 3)
            image = image.crop((0, top, image.width, top + new_height))
        image = image.resize((width, height))
        output = BytesIO()
        image.save(output, format="PNG", optimize=True)
        return output.getvalue()
    except Exception:
        return _placeholder_photo(width, height)


def _section_title(c: canvas.Canvas, x: float, y: float, width: float, title: str, color=DARK) -> None:
    c.setFillColor(color)
    c.rect(x, y - 17, width, 18, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 8.2)
    c.drawCentredString(x + width / 2, y - 11, title.upper())


def _card(c: canvas.Canvas, x: float, y: float, width: float, height: float, fill=WHITE) -> None:
    c.setFillColor(fill)
    c.setStrokeColor(colors.HexColor("#BFC5CE"))
    c.setLineWidth(.55)
    c.roundRect(x, y - height, width, height, 5, fill=1, stroke=1)


def _metric(c: canvas.Canvas, x: float, y: float, width: float, label: str, value: str, accent=LIGHT, sub: str = "") -> None:
    _card(c, x, y, width, 42, WHITE)
    c.setFillColor(accent)
    c.rect(x, y - 42, 4, 42, fill=1, stroke=0)
    c.setFillColor(TEXT)
    c.setFont("Helvetica-Bold", 6.2)
    c.drawString(x + 9, y - 11, label.upper())
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(x + 9, y - 27, value)
    if sub:
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 5.7)
        c.drawRightString(x + width - 7, y - 36, sub)


def _transfer_color(value: float | None):
    if value is None:
        return colors.HexColor("#94A3B8")
    if value >= 85:
        return GREEN
    if value >= 70:
        return ORANGE
    return RED


def _draw_wrapped(c: canvas.Canvas, text: str, x: float, y: float, width: float, max_lines: int, size: float = 7.4, leading: float = 9.2) -> None:
    words = (text or "").replace("\n", " \n ").split()
    lines: list[str] = []
    current = ""
    for word in words:
        if word == "\n":
            lines.append(current)
            current = ""
            continue
        trial = f"{current} {word}".strip()
        if stringWidth(trial, "Helvetica", size) <= width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    c.setFillColor(TEXT)
    c.setFont("Helvetica", size)
    for line in lines[:max_lines]:
        c.drawString(x, y, line)
        y -= leading


def _season_label(year: int, month: int) -> str:
    start = year if month >= 7 else year - 1
    return f"{start}-{start + 1}"


def build_report_pdf(data: dict, stats: dict) -> bytes:
    player = data["player"]
    attendance = stats["attendance"]
    shooting = stats["shooting"]
    progression = stats["progression"]

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    margin = 22
    content_w = PAGE_W - 2 * margin

    # ------------------------------------------------------------------
    # EN-TÊTE IDENTITAIRE - inspiré de l'ancien rapport
    # ------------------------------------------------------------------
    header_bottom = PAGE_H - 146
    c.setFillColor(colors.HexColor("#F7F7F9"))
    c.rect(0, header_bottom, PAGE_W, PAGE_H - header_bottom, fill=1, stroke=0)

    if LOGO_PATH.exists():
        c.drawImage(str(LOGO_PATH), 22, PAGE_H - 104, width=94, height=78, preserveAspectRatio=True, anchor="c", mask="auto")

    c.setFillColor(GOLD)
    c.rect(118, PAGE_H - 42, PAGE_W - 140, 4, fill=1, stroke=0)
    c.rect(118, PAGE_H - 92, PAGE_W - 140, 4, fill=1, stroke=0)

    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 15.5)
    title_center = (118 + (PAGE_W - 127)) / 2
    c.drawCentredString(title_center, PAGE_H - 68, f"BILAN MENSUEL - {MONTH_NAMES[data['month']]} {data['year']}")

    # Identité joueur
    identity_x = 118
    identity_y = PAGE_H - 106
    identity_w = PAGE_W - 118 - 112 - 22
    _card(c, identity_x, identity_y, identity_w, 43, CARD)
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(identity_x + identity_w / 2, identity_y - 14, player_label(player).upper())
    c.setFont("Helvetica", 6.8)
    details_left = f"Poste : {(player.get('position') or '—').upper()}   |   Catégorie : {player.get('category') or '—'}"
    details_right = f"Saison : {_season_label(data['year'], data['month'])}   |   Mois : {MONTH_NAMES[data['month']].title()}"
    c.drawString(identity_x + 10, identity_y - 29, details_left)
    c.drawRightString(identity_x + identity_w - 10, identity_y - 29, details_right)

    # Photo rectangulaire
    photo_x, photo_y, photo_w, photo_h = PAGE_W - 117, PAGE_H - 143, 90, 88
    photo_raw = _download_image(player.get("photo_url")) or _placeholder_photo()
    photo = _fit_photo_rect(photo_raw)
    c.setStrokeColor(GOLD)
    c.setLineWidth(1.4)
    c.rect(photo_x - 2, photo_y - 2, photo_w + 4, photo_h + 4, fill=0, stroke=1)
    c.drawImage(ImageReader(BytesIO(photo)), photo_x, photo_y, width=photo_w, height=photo_h, preserveAspectRatio=False, mask="auto")

    # ------------------------------------------------------------------
    # 1. ASSIDUITÉ + 2. SYNTHÈSE DES 4 CONTEXTES
    # ------------------------------------------------------------------
    y = header_bottom - 10
    left_w = 190
    gap = 10
    right_x = margin + left_w + gap
    right_w = content_w - left_w - gap

    _section_title(c, margin, y, left_w, "1. Assiduité", LIGHT)
    _section_title(c, right_x, y, right_w, "2. Synthèse des contextes de tir", GOLD)
    y -= 23

    # Assiduité
    _card(c, margin, y, left_w, 103, WHITE)
    c.setFillColor(TEXT)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(margin + 10, y - 14, "PRÉSENCE")
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 18)
    c.drawRightString(margin + left_w - 10, y - 16, f"{attendance['present']} / {attendance['total']}")
    c.setFillColor(TEXT)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(margin + 10, y - 38, "% PRÉSENCES")
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 18)
    c.drawRightString(margin + left_w - 10, y - 40, f"{attendance['rate']:.0f} %")
    c.setStrokeColor(LINE)
    c.line(margin + 10, y - 51, margin + left_w - 10, y - 51)
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 6.5)
    c.drawString(margin + 10, y - 66, f"Blessure / maladie / études : {attendance['excused']}")
    c.drawString(margin + 10, y - 82, f"Autres absences : {attendance['absent']}")

    # 4 contextes
    _card(c, right_x, y, right_w, 103, WHITE)
    context_card_w = (right_w - 30) / 4
    context_colors = [GOLD, DARK, LIGHT, DARK]
    for index, context in enumerate(CONTEXTS):
        values = shooting["by_context"][context]
        x = right_x + 6 + index * (context_card_w + 6)
        c.setFillColor(colors.HexColor("#F7F7F9"))
        c.roundRect(x, y - 68, context_card_w, 58, 4, fill=1, stroke=0)
        c.setFillColor(context_colors[index])
        c.rect(x, y - 15, context_card_w, 5, fill=1, stroke=0)
        label_lines = CONTEXTS[context].replace("En mouvement", "Mouvement").split(" ")
        c.setFillColor(TEXT)
        c.setFont("Helvetica-Bold", 5.5)
        first_line = " ".join(label_lines[:2])
        second_line = " ".join(label_lines[2:])
        c.drawCentredString(x + context_card_w / 2, y - 28, first_line.upper())
        if second_line:
            c.drawCentredString(x + context_card_w / 2, y - 36, second_line.upper())
        c.setFillColor(DARK)
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(x + context_card_w / 2, y - 52, f"{values['pct']:.1f} %")
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 5.5)
        c.drawCentredString(x + context_card_w / 2, y - 62, f"{int(values['made'])}/{int(values['attempted'])}")

    transfers = shooting["transfers"]
    transfer_y = y - 76
    transfer_labels = [
        ("Passage au mouvement", transfers["passage_mouvement"]),
        ("Opposition - statique", transfers["opposition_statique"]),
        ("Opposition - mouvement", transfers["opposition_mouvement"]),
    ]
    transfer_w = (right_w - 16) / 3
    for index, (label, value) in enumerate(transfer_labels):
        x = right_x + 4 + index * (transfer_w + 4)
        c.setFillColor(_transfer_color(value))
        c.roundRect(x, transfer_y - 21, transfer_w, 20, 3, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 5.4)
        c.drawString(x + 5, transfer_y - 9, label.upper())
        c.setFont("Helvetica-Bold", 8)
        c.drawRightString(x + transfer_w - 5, transfer_y - 10, "—" if value is None else f"{value:.0f} %")

    # ------------------------------------------------------------------
    # 3. DEUX RADARS
    # ------------------------------------------------------------------
    y -= 119
    _section_title(c, margin, y, content_w, "3. Performance par spot et contexte", DARK)
    y -= 22

    radar_gap = 10
    radar_w = (content_w - radar_gap) / 2
    radar_h = 186
    _card(c, margin, y, radar_w, radar_h, WHITE)
    _card(c, margin + radar_w + radar_gap, y, radar_w, radar_h, WHITE)

    zone_context = shooting["by_zone_context"]
    static_free = [float(zone_context[zone]["statique_sans_opposition"]["pct"]) for zone in ZONES]
    static_opp = [float(zone_context[zone]["statique_avec_opposition"]["pct"]) for zone in ZONES]
    movement_free = [float(zone_context[zone]["mouvement_sans_opposition"]["pct"]) for zone in ZONES]
    movement_opp = [float(zone_context[zone]["mouvement_avec_opposition"]["pct"]) for zone in ZONES]

    static_radar = radar_comparison_chart(
        list(ZONES), static_free, static_opp,
        "Sans opposition", "Avec opposition", "#B8A05A", "#1A2434",
    )
    movement_radar = radar_comparison_chart(
        list(ZONES), movement_free, movement_opp,
        "Sans opposition", "Avec opposition", "#04B3EA", "#1A2434",
    )

    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(margin + radar_w / 2, y - 13, "TIR STATIQUE")
    c.drawCentredString(margin + radar_w + radar_gap + radar_w / 2, y - 13, "TIR EN MOUVEMENT")
    c.drawImage(ImageReader(BytesIO(static_radar)), margin + 6, y - radar_h + 4, width=radar_w - 12, height=radar_h - 23, preserveAspectRatio=True, anchor="c", mask="auto")
    c.drawImage(ImageReader(BytesIO(movement_radar)), margin + radar_w + radar_gap + 6, y - radar_h + 4, width=radar_w - 12, height=radar_h - 23, preserveAspectRatio=True, anchor="c", mask="auto")

    # ------------------------------------------------------------------
    # 4. PROGRESSION + STABILITÉ
    # ------------------------------------------------------------------
    y -= radar_h + 8
    _section_title(c, margin, y, content_w, "4. Progression saisonnière et stabilité", GOLD)
    y -= 22

    chart_w = 350
    stab_x = margin + chart_w + 10
    stab_w = content_w - chart_w - 10
    block_h = 104
    _card(c, margin, y, chart_w, block_h, WHITE)
    _card(c, stab_x, y, stab_w, block_h, WHITE)
    progression_png = progression_chart(progression[-8:])
    c.drawImage(ImageReader(BytesIO(progression_png)), margin + 5, y - block_h + 4, width=chart_w - 10, height=block_h - 8, preserveAspectRatio=True, anchor="c", mask="auto")

    stability = shooting["stability"]
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(stab_x + 10, y - 15, "STABILITÉ GLOBALE DU TIR")
    if stability["score"] is None:
        c.setFont("Helvetica-Bold", 13)
        c.drawString(stab_x + 10, y - 41, stability["label"])
    else:
        c.setFont("Helvetica-Bold", 22)
        c.drawString(stab_x + 10, y - 43, f"{stability['score']:.0f} / 100")
        c.setFillColor(_transfer_color(stability["score"]))
        c.setFont("Helvetica-Bold", 8)
        c.drawString(stab_x + 10, y - 58, stability["label"])
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 6.4)
    c.drawString(stab_x + 10, y - 76, f"Séances analysées : {stability['sessions']}")
    c.drawString(stab_x + 10, y - 89, f"Écart-type : {'—' if stability['std_dev'] is None else str(stability['std_dev']) + ' pts'}")

    # ------------------------------------------------------------------
    # 5. COMMENTAIRE
    # ------------------------------------------------------------------
    y -= block_h + 8
    _section_title(c, margin, y, content_w, "5. Commentaire du staff", DARK)
    y -= 22
    comment_h = max(63, y - 30)
    _card(c, margin, y, content_w, comment_h, WHITE)
    comment = (data.get("staff_comment") or {}).get("comment") or "Aucun commentaire renseigné pour ce mois."
    _draw_wrapped(c, comment, margin + 12, y - 16, content_w - 24, 6, size=7.3, leading=9.1)
    author = (data.get("staff_comment") or {}).get("author")
    if author:
        c.setFillColor(GOLD)
        c.setFont("Helvetica-Bold", 6.5)
        c.drawRightString(PAGE_W - margin - 10, y - comment_h + 10, f"- {author}")

    c.setFillColor(DARK)
    c.rect(0, 0, PAGE_W, 14, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica", 5.7)
    c.drawCentredString(PAGE_W / 2, 4.5, "CHAMPAGNE PERFORMANCE - DOCUMENT INTERNE AU CENTRE DE FORMATION")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()
