from pathlib import Path


SCHEMA_SQL = Path(__file__).resolve().parents[3] / "infra" / "postgres" / "001_init.sql"


def test_atlas_tables_enable_rls():
    sql = SCHEMA_SQL.read_text(encoding="utf-8").lower()

    for table in [
        "atlas_profiles",
        "atlas_subscriptions",
        "atlas_research_runs",
        "atlas_reports",
        "atlas_watchlist_items",
        "atlas_usage_events",
    ]:
        assert f"alter table public.{table} enable row level security" in sql


def test_user_owned_tables_have_user_indexes_and_auth_uid_policies():
    sql = SCHEMA_SQL.read_text(encoding="utf-8").lower()

    for table in [
        "atlas_subscriptions",
        "atlas_research_runs",
        "atlas_reports",
        "atlas_watchlist_items",
        "atlas_usage_events",
    ]:
        assert f"on public.{table} using btree (user_id" in sql

    assert "(select auth.uid()) = user_id" in sql
    assert "(select auth.uid()) = id" in sql
