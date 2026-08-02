from __future__ import annotations

from services.report_data import load_player_report_data
from services.report_pdf import build_report_pdf
from services.report_stats import build_report_stats


def build_player_report(player: dict, year: int, month: int) -> bytes:
    data = load_player_report_data(player, year, month)
    stats = build_report_stats(data)
    return build_report_pdf(data, stats)
