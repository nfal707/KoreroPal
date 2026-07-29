import pandas as pd


def daily_summary(df):
    if df.empty:
        return "No check-ins yet."

    mood_avg = round(df["mood"].mean(), 2)
    stress_avg = round(df["stress"].mean(), 2)
    energy_avg = round(df["energy"].mean(), 2)

    return (
        f"Average mood: {mood_avg}/7\n"
        f"Average stress: {stress_avg}/7\n"
        f"Average energy: {energy_avg}/7"
    )


def add_change_columns(df):
    if df.empty:
        return df

    result = df.copy()
    result["mood_change"] = result["mood_after"] - result["mood_before"]
    result["stress_improvement"] = result["stress_before"] - result["stress_after"]
    result["energy_change"] = result["energy_after"] - result["energy_before"]
    return result


def evaluation_summary(df):
    if df.empty:
        return "No completed AI evaluations yet."

    result = add_change_columns(df)

    mood_change = round(result["mood_change"].mean(), 2)
    stress_improvement = round(result["stress_improvement"].mean(), 2)
    energy_change = round(result["energy_change"].mean(), 2)
    felt_heard = round(result["felt_heard"].mean(), 2)
    relevance = round(result["response_relevance"].mean(), 2)
    reuse = round(result["would_use_again"].mean(), 2)

    return (
        f"Average mood change: {mood_change:+}/7\n"
        f"Average stress improvement: {stress_improvement:+}/7\n"
        f"Average energy change: {energy_change:+}/7\n"
        f"Average felt heard rating: {felt_heard}/7\n"
        f"Average response relevance: {relevance}/7\n"
        f"Average willingness to use again: {reuse}/7"
    )


def recent_context_from_checkins(df, limit=3):
    if df.empty:
        return "No recent check-ins."

    recent = df.tail(limit)
    lines = []

    for _, row in recent.iterrows():
        lines.append(
            f"- {row['created_at']}: mood {row['mood']}/7, "
            f"stress {row['stress']}/7, energy {row['energy']}/7"
        )

    return "\n".join(lines)
