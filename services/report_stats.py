from __future__ import annotations

from collections import defaultdict
from datetime import date
from statistics import pstdev
from typing import Any

CONTEXTS = {
    "statique_sans_opposition": "Statique sans opposition",
    "statique_avec_opposition": "Statique avec opposition",
    "mouvement_sans_opposition": "En mouvement sans opposition",
    "mouvement_avec_opposition": "En mouvement avec opposition",
}

CONTEXT_ORDER = tuple(CONTEXTS.keys())
ZONES = ("0G", "45G", "70G", "AXE", "70D", "45D", "0D")

PRESENT_STATUSES = {"Présent", "Avec les professionnels"}
EXCUSED_STATUSES = {"Blessé", "Malade", "Formation / Études"}


def safe_pct(made: int, attempted: int) -> float:
    return round((made / attempted) * 100, 1) if attempted else 0.0


def transfer_index(target_pct: float, reference_pct: float) -> float | None:
    """Part de la performance de référence conservée dans la situation cible."""
    if reference_pct <= 0:
        return None
    return round((target_pct / reference_pct) * 100, 1)


def attendance_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        counts[str(row.get("status") or "Non renseigné")] += 1

    total = sum(counts.values())
    present = sum(counts[status] for status in PRESENT_STATUSES)
    excused = sum(counts[status] for status in EXCUSED_STATUSES)
    absent = max(0, total - present - excused)

    return {
        "total": total,
        "present": present,
        "excused": excused,
        "absent": absent,
        "rate": safe_pct(present, total),
        "counts": dict(counts),
    }


def shooting_stats(sessions: list[dict[str, Any]]) -> dict[str, Any]:
    by_context: dict[str, dict[str, int | float]] = {
        context: {"made": 0, "attempted": 0, "pct": 0.0}
        for context in CONTEXT_ORDER
    }
    by_zone_context: dict[str, dict[str, dict[str, int | float]]] = {
        zone: {
            context: {"made": 0, "attempted": 0, "pct": 0.0}
            for context in CONTEXT_ORDER
        }
        for zone in ZONES
    }

    session_percentages: list[float] = []
    total_duration = 0
    total_made = 0
    total_attempted = 0

    for session in sessions:
        total_duration += int(session.get("duration_seconds") or 0)
        session_made = 0
        session_attempted = 0

        for result in session.get("shooting_results") or []:
            context = str(result.get("context") or "statique_sans_opposition")
            if context not in CONTEXTS:
                context = "statique_sans_opposition"

            zone = str(result.get("zone") or "")
            attempted = int(result.get("attempted") or 0)
            made = int(result.get("made") or 0)

            by_context[context]["made"] += made
            by_context[context]["attempted"] += attempted

            if zone in by_zone_context:
                by_zone_context[zone][context]["made"] += made
                by_zone_context[zone][context]["attempted"] += attempted

            session_made += made
            session_attempted += attempted
            total_made += made
            total_attempted += attempted

        if session_attempted:
            session_percentages.append((session_made / session_attempted) * 100)

    for values in by_context.values():
        values["pct"] = safe_pct(int(values["made"]), int(values["attempted"]))

    for zone_values in by_zone_context.values():
        for values in zone_values.values():
            values["pct"] = safe_pct(int(values["made"]), int(values["attempted"]))

    static_free = float(by_context["statique_sans_opposition"]["pct"])
    static_opposed = float(by_context["statique_avec_opposition"]["pct"])
    movement_free = float(by_context["mouvement_sans_opposition"]["pct"])
    movement_opposed = float(by_context["mouvement_avec_opposition"]["pct"])

    transfers = {
        "passage_mouvement": transfer_index(movement_free, static_free),
        "opposition_statique": transfer_index(static_opposed, static_free),
        "opposition_mouvement": transfer_index(movement_opposed, movement_free),
    }

    return {
        "sessions": len(sessions),
        "duration_seconds": total_duration,
        "made": total_made,
        "attempted": total_attempted,
        "pct": safe_pct(total_made, total_attempted),
        "by_context": by_context,
        "by_zone_context": by_zone_context,
        "transfers": transfers,
        "stability": stability_stats(session_percentages),
    }


def stability_stats(values: list[float]) -> dict[str, Any]:
    if not values:
        return {
            "score": None,
            "label": "Données insuffisantes",
            "std_dev": None,
            "sessions": 0,
        }
    if len(values) == 1:
        return {
            "score": None,
            "label": "Non interprétable",
            "std_dev": None,
            "sessions": 1,
        }

    deviation = pstdev(values)
    score = max(0.0, min(100.0, 100.0 - deviation * 4.0))
    if score >= 80:
        label = "Très stable"
    elif score >= 65:
        label = "Stable"
    elif score >= 45:
        label = "Irrégulier"
    else:
        label = "Très irrégulier"

    return {
        "score": round(score, 1),
        "label": label,
        "std_dev": round(deviation, 1),
        "sessions": len(values),
    }


def season_progression(sessions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    monthly: dict[tuple[int, int], dict[str, int]] = defaultdict(
        lambda: {"made": 0, "attempted": 0}
    )

    for session in sessions:
        raw_date = session.get("session_date")
        if not raw_date:
            continue
        parsed = date.fromisoformat(str(raw_date)[:10])
        key = (parsed.year, parsed.month)
        for result in session.get("shooting_results") or []:
            monthly[key]["made"] += int(result.get("made") or 0)
            monthly[key]["attempted"] += int(result.get("attempted") or 0)

    return [
        {
            "year": year,
            "month": month,
            "label": f"{month:02d}/{str(year)[2:]}",
            "made": values["made"],
            "attempted": values["attempted"],
            "pct": safe_pct(values["made"], values["attempted"]),
        }
        for (year, month), values in sorted(monthly.items())
    ]


def build_report_stats(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "attendance": attendance_stats(data["attendance"]),
        "shooting": shooting_stats(data["shooting"]),
        "progression": season_progression(data["season_shooting"]),
    }
