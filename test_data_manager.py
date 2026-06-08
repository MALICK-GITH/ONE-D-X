from pathlib import Path

from config import get_config
from one_delux_fast.api_client import Event
from one_delux_fast.data_manager import DataManager


def _make_event() -> Event:
    return Event(
        event_id=12345,
        sport_id=85,
        sport_name="FIFA",
        league_id=7,
        league_name="Test League",
        team1_id=1001,
        team1_name="Alpha FC",
        team2_id=1002,
        team2_name="Beta FC",
        start_time=1710000000,
        is_live=False,
        score=None,
        odds=[],
        additional_odds=[],
        country="FR",
        last_update=1710000000,
    )


def test_get_database_path_accepts_absolute_paths(tmp_path):
    config = get_config()
    original_path = config.database.path

    try:
        absolute_db = tmp_path / "custom.db"
        config.database.path = str(absolute_db)

        assert config.get_database_path() == str(absolute_db)
    finally:
        config.database.path = original_path


def test_get_events_with_cache_uses_fetcher_and_reuses_cache(tmp_path):
    config = get_config()
    original_path = config.database.path

    try:
        config.database.path = str(tmp_path / "events.db")
        manager = DataManager()

        calls = {"count": 0}
        event = _make_event()

        def fetcher():
            calls["count"] += 1
            return [event]

        first_result = manager.get_events_with_cache(fetcher=fetcher)
        second_result = manager.get_events_with_cache()

        assert first_result == [event]
        assert second_result == [event]
        assert first_result is second_result
        assert calls["count"] == 1
        assert Path(manager.database.db_path).exists()
    finally:
        config.database.path = original_path
