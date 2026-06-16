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


def test_backend_owned_tables_are_not_writable_by_authenticated_role():
    sql = SCHEMA_SQL.read_text(encoding="utf-8").lower()

    forbidden_fragments = [
        "grant select, insert, update, delete on public.atlas_research_runs to authenticated",
        "grant select, insert, update, delete on public.atlas_reports to authenticated",
        "grant select, insert on public.atlas_usage_events to authenticated",
        "on public.atlas_research_runs for insert to authenticated",
        "on public.atlas_research_runs for update to authenticated",
        "on public.atlas_reports for insert to authenticated",
        "on public.atlas_usage_events for insert to authenticated",
    ]

    for fragment in forbidden_fragments:
        assert fragment not in sql


def test_security_definer_function_has_locked_search_path():
    sql = SCHEMA_SQL.read_text(encoding="utf-8").lower()

    assert "security definer\nset search_path = ''" in sql
