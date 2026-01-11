"""
Analytics Blueprint for In-Tuned
Provides emotion trends, activity stats, and insights
"""

from datetime import datetime, timedelta
from flask import Blueprint, g
from collections import defaultdict

from app.utils.responses import api_response, api_error
from app.utils.security import require_login
from app.db.repositories.journal_repository import JournalRepository


bp = Blueprint("analytics", __name__, url_prefix="/api/analytics")


def parse_period(period: str) -> datetime:
    """Parse period string to start date."""
    now = datetime.utcnow()

    if period == "7d":
        return now - timedelta(days=7)
    elif period == "30d":
        return now - timedelta(days=30)
    elif period == "90d":
        return now - timedelta(days=90)
    elif period == "365d" or period == "1y":
        return now - timedelta(days=365)
    elif period == "all":
        return datetime(2000, 1, 1)  # Far in the past
    else:
        return now - timedelta(days=30)  # Default to 30 days


@bp.route("/emotions", methods=["GET"])
@require_login
def get_emotion_trends():
    """Get emotion distribution and trends for the current user."""
    from flask import request

    user_id = g.user["id"]
    period = request.args.get("period", "30d")
    start_date = parse_period(period)

    repo = JournalRepository()

    # Get all journals for user in period
    journals = repo.find_by_user(user_id, page=1, per_page=10000)

    # Filter by date
    filtered = []
    for journal in journals:
        created = journal.get("created_at")
        if created:
            if isinstance(created, str):
                try:
                    created = datetime.fromisoformat(created.replace("Z", "+00:00"))
                except ValueError:
                    continue
            if created.replace(tzinfo=None) >= start_date:
                filtered.append(journal)

    # Calculate emotion distribution
    distribution = defaultdict(float)
    total_weight = 0

    for journal in filtered:
        analysis = journal.get("analysis_json", {})
        if not analysis:
            continue

        core_mixture = analysis.get("coreMixture", [])

        # Handle both array and object formats
        if isinstance(core_mixture, list):
            for item in core_mixture:
                emotion = item.get("id") or item.get("label", "").lower()
                percent = item.get("percent", 0)
                if emotion and percent:
                    distribution[emotion] += percent
                    total_weight += percent
        elif isinstance(core_mixture, dict):
            for emotion, value in core_mixture.items():
                if isinstance(value, dict):
                    percent = value.get("percent", 0)
                else:
                    percent = float(value) * 100 if value <= 1 else float(value)
                if percent:
                    distribution[emotion] += percent
                    total_weight += percent

    # Normalize to percentages
    if total_weight > 0:
        for emotion in distribution:
            distribution[emotion] = round((distribution[emotion] / total_weight) * 100, 1)

    # Calculate weekly trends
    weekly_data = defaultdict(lambda: defaultdict(int))

    for journal in filtered:
        created = journal.get("created_at")
        if isinstance(created, str):
            try:
                created = datetime.fromisoformat(created.replace("Z", "+00:00"))
            except ValueError:
                continue

        # Get week start
        week_start = created - timedelta(days=created.weekday())
        week_key = week_start.strftime("%Y-%m-%d")

        analysis = journal.get("analysis_json", {})
        results = analysis.get("results", {})
        dominant = results.get("dominant", {})

        if isinstance(dominant, dict):
            emotion = dominant.get("id") or dominant.get("label", "").lower()
        else:
            emotion = str(dominant).lower()

        if emotion:
            weekly_data[week_key][emotion] += 1

    trends = [
        {"date": date, "emotions": dict(emotions)}
        for date, emotions in sorted(weekly_data.items())
    ]

    return api_response({
        "distribution": dict(distribution),
        "trends": trends,
        "totalEntries": len(filtered),
        "period": period
    })


@bp.route("/activity", methods=["GET"])
@require_login
def get_activity_stats():
    """Get activity statistics for the current user."""
    from flask import request

    user_id = g.user["id"]
    period = request.args.get("period", "30d")
    start_date = parse_period(period)

    repo = JournalRepository()

    # Get all journals for user
    journals = repo.find_by_user(user_id, page=1, per_page=10000)

    # Group by day
    daily_counts = defaultdict(int)

    for journal in journals:
        created = journal.get("created_at")
        if created:
            if isinstance(created, str):
                try:
                    created = datetime.fromisoformat(created.replace("Z", "+00:00"))
                except ValueError:
                    continue

            if created.replace(tzinfo=None) >= start_date:
                day_key = created.strftime("%Y-%m-%d")
                daily_counts[day_key] += 1

    # Convert to sorted list
    daily = [
        {"date": date, "count": count}
        for date, count in sorted(daily_counts.items())
    ]

    # Calculate current streak
    streak = 0
    today = datetime.utcnow().date()
    current_date = today

    while True:
        date_key = current_date.strftime("%Y-%m-%d")
        if daily_counts.get(date_key, 0) > 0:
            streak += 1
            current_date -= timedelta(days=1)
        else:
            break

    # Calculate average entries per week
    if daily:
        first_date = datetime.strptime(daily[0]["date"], "%Y-%m-%d").date()
        days_span = max(1, (today - first_date).days)
        weeks = max(1, days_span / 7)
        avg_per_week = round(len(journals) / weeks, 1)
    else:
        avg_per_week = 0

    return api_response({
        "daily": daily,
        "streak": streak,
        "avgPerWeek": avg_per_week,
        "totalDays": len(daily_counts),
        "period": period
    })


@bp.route("/insights", methods=["GET"])
@require_login
def get_insights():
    """Generate insights for the current user."""
    user_id = g.user["id"]

    repo = JournalRepository()
    journals = repo.find_by_user(user_id, page=1, per_page=10000)

    insights = []

    if not journals:
        insights.append({
            "type": "info",
            "title": "Get Started",
            "message": "Create your first journal entry to start tracking your emotions."
        })
        return api_response({"insights": insights})

    # Analyze emotion patterns
    emotion_counts = defaultdict(int)
    total_analyzed = 0

    for journal in journals:
        analysis = journal.get("analysis_json", {})
        results = analysis.get("results", {})
        dominant = results.get("dominant", {})

        if isinstance(dominant, dict):
            emotion = dominant.get("label") or dominant.get("id")
        else:
            emotion = dominant

        if emotion:
            emotion_counts[str(emotion).lower()] += 1
            total_analyzed += 1

    # Most common emotion insight
    if emotion_counts:
        sorted_emotions = sorted(
            emotion_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        top_emotion, count = sorted_emotions[0]
        percentage = round((count / total_analyzed) * 100)

        insights.append({
            "type": "highlight",
            "title": "Dominant Emotion",
            "message": f"{top_emotion.capitalize()} appears in {percentage}% of your entries."
        })

        # Emotional diversity
        unique_count = len(emotion_counts)
        if unique_count >= 5:
            insights.append({
                "type": "positive",
                "title": "Emotional Range",
                "message": f"You've experienced {unique_count} different dominant emotions. "
                          "This emotional diversity is healthy!"
            })
        elif unique_count <= 2:
            insights.append({
                "type": "info",
                "title": "Emotional Pattern",
                "message": "Your entries show a focused emotional pattern. "
                          "Consider exploring what drives these feelings."
            })

    # Journaling frequency
    if len(journals) >= 2:
        first_entry = journals[-1]
        last_entry = journals[0]

        first_date = first_entry.get("created_at")
        last_date = last_entry.get("created_at")

        if first_date and last_date:
            if isinstance(first_date, str):
                first_date = datetime.fromisoformat(first_date.replace("Z", "+00:00"))
            if isinstance(last_date, str):
                last_date = datetime.fromisoformat(last_date.replace("Z", "+00:00"))

            days_span = max(1, (last_date - first_date).days)
            avg_per_week = round((len(journals) / days_span) * 7, 1)

            insights.append({
                "type": "stat",
                "title": "Writing Frequency",
                "message": f"You write an average of {avg_per_week} entries per week."
            })

    # Milestone insights
    milestones = [10, 25, 50, 100, 250, 500, 1000]
    for milestone in milestones:
        if len(journals) >= milestone and len(journals) < milestone + 10:
            insights.append({
                "type": "achievement",
                "title": "Milestone Reached!",
                "message": f"Congratulations on reaching {milestone} journal entries!"
            })
            break

    return api_response({"insights": insights})
