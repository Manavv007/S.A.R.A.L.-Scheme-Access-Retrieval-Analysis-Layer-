"""Unit tests for scraper/saral_scraper/statestore.py."""

from saral_scraper.statestore import StateStore


def test_incremental_change_detection(tmp_path):
    db = str(tmp_path / "state.sqlite")
    store = StateStore(db)

    # New scheme -> changed (not seen before)
    assert store.has_changed("central-pm-kisan", "h1") is True
    store.record("central-pm-kisan", "h1", "2026-01-01", "https://x", "PM-KISAN")

    # Same hash -> unchanged
    assert store.has_changed("central-pm-kisan", "h1") is False
    # New hash -> changed
    assert store.has_changed("central-pm-kisan", "h2") is True

    assert store.count() == 1
    assert store.get_hash("central-pm-kisan") == "h1"
    store.close()


def test_record_upsert(tmp_path):
    db = str(tmp_path / "state.sqlite")
    store = StateStore(db)
    store.record("s1", "a", "t1")
    store.record("s1", "b", "t2")  # upsert, not duplicate
    assert store.count() == 1
    assert store.get_hash("s1") == "b"
    store.close()
