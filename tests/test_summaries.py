import pandas as pd

from core.summaries import add_change_columns


def test_change_columns():
    df = pd.DataFrame(
        [
            {
                "mood_before": 3,
                "mood_after": 5,
                "stress_before": 6,
                "stress_after": 4,
                "energy_before": 2,
                "energy_after": 3,
            }
        ]
    )

    result = add_change_columns(df)

    assert result.iloc[0]["mood_change"] == 2
    assert result.iloc[0]["stress_improvement"] == 2
    assert result.iloc[0]["energy_change"] == 1
