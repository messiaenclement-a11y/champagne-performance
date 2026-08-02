from __future__ import annotations

from datetime import date
from typing import Any

from services.supabase_client import get_supabase


def month_bounds(year: int, month: int) -> tuple[date, date]:
    start = date(year, month, 1)
    end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    return start, end


def load_player_report_data(player: dict[str, Any], year: int, month: int) -> dict[str, Any]:
    start, end = month_bounds(year, month)
    db = get_supabase()

    attendance = (
        db.table("attendance_records")
        .select("status,comment,attendance_sessions!inner(session_date,session_time,title,session_type)")
        .eq("player_id", player["id"])
        .gte("attendance_sessions.session_date", start.isoformat())
        .lt("attendance_sessions.session_date", end.isoformat())
        .execute().data
        or []
    )

    shooting = (
        db.table("shooting_sessions")
        .select("id,session_date,duration_seconds,comment,shooting_results(zone,context,attempted,made)")
        .eq("player_id", player["id"])
        .gte("session_date", start.isoformat())
        .lt("session_date", end.isoformat())
        .order("session_date")
        .execute().data
        or []
    )

    season_start_year = year if month >= 7 else year - 1
    season_start = date(season_start_year, 7, 1)
    season_shooting = (
        db.table("shooting_sessions")
        .select("session_date,shooting_results(context,attempted,made)")
        .eq("player_id", player["id"])
        .gte("session_date", season_start.isoformat())
        .lt("session_date", end.isoformat())
        .order("session_date")
        .execute().data
        or []
    )

    comments = (
        db.table("staff_comments")
        .select("comment,author,updated_at")
        .eq("player_id", player["id"])
        .eq("report_month", start.isoformat())
        .limit(1)
        .execute().data
        or []
    )

    return {
        "player": player,
        "year": year,
        "month": month,
        "start": start,
        "end": end,
        "attendance": attendance,
        "shooting": shooting,
        "season_shooting": season_shooting,
        "staff_comment": comments[0] if comments else {},
    }
