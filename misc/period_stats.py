import pandas as pd
from datetime import timedelta
from pathlib import Path
from pandas.api.types import DatetimeTZDtype
import sys

# Ensure repository root is on sys.path so imports work when running this script directly
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import config  # now resolvable

# Reuse logic from the dashboard to ensure identical results
from web_dashboard import _aggregate_productivity_from_commits, filter_commits_by_period


def load_commits_df(commits_csv: str) -> pd.DataFrame:
    """Load commits with the same normalization as web_dashboard.py (date_day, bools, tz)."""
    commits = pd.read_csv(commits_csv, parse_dates=['date'])

    # Convert boolean string columns to integers
    bool_cols = ['has_issue_ref', 'follows_convention', 'is_merge', 'is_revert', 'is_hotfix', 'has_breaking_change']
    for col in bool_cols:
        if col in commits.columns:
            commits[col] = commits[col].map({'TRUE': 1, 'FALSE': 0}).fillna(0).astype(int)

    # Drop timezone to avoid period conversion issues
    try:
        if isinstance(commits['date'].dtype, DatetimeTZDtype):
            if commits['date'].dt.tz is not None:
                commits['date'] = commits['date'].dt.tz_convert('UTC').dt.tz_localize(None)
            else:
                commits['date'] = commits['date'].dt.tz_localize(None)
    except Exception:
        try:
            commits['date'] = commits['date'].dt.tz_localize(None)
        except Exception:
            pass

    # Stable date-only column (avoid tz edge cases)
    try:
        commits_raw = pd.read_csv(commits_csv, dtype={'date': str})
        commits['date_day'] = pd.to_datetime(commits_raw['date'].str.slice(0, 10), format='%Y-%m-%d', errors='coerce')
    except Exception:
        commits['date_day'] = commits['date'].dt.normalize()

    return commits


def filter_last_4_weeks(commits_df: pd.DataFrame) -> pd.DataFrame:
    """Filter commits to the last 28 days using the same end-date anchor as the dashboard."""
    base_col = 'date_day' if 'date_day' in commits_df.columns else 'date'
    end_date = commits_df[base_col].max()
    start_date = end_date - timedelta(days=28)
    return commits_df[commits_df[base_col] >= start_date]


def describe_period(df: pd.DataFrame) -> str:
    if df.empty:
        return 'N/A'
    base_col = 'date_day' if 'date_day' in df.columns else 'date'
    return f"{df[base_col].min().strftime('%Y-%m-%d')} to {df[base_col].max().strftime('%Y-%m-%d')}"


def _build_complete_index(devs, dates):
    import itertools
    return pd.MultiIndex.from_tuples(list(itertools.product(devs, dates)), names=['developer', 'when'])


def daily_timeseries_last_7(commits_df: pd.DataFrame) -> pd.DataFrame:
    """Per-developer daily series for the last 7 days (inclusive), with zero-filled gaps for commits.
    Columns: date, developer, commits, lines_added, lines_deleted, total_changes, avg_quality,
             issue_refs, conventional_commits, hotfixes, merges, reverts, breaking_changes,
             issue_ref_rate, conventional_rate, hotfix_rate, merge_rate, revert_rate, breaking_rate,
             avg_lines_per_commit
    """
    if commits_df.empty:
        return pd.DataFrame()
    base_dt = commits_df['date_day'] if 'date_day' in commits_df.columns else commits_df['date'].dt.normalize()
    end_date = base_dt.max()
    start_date = end_date - pd.Timedelta(days=7)
    df = commits_df[base_dt >= start_date].copy()
    if df.empty:
        return pd.DataFrame()
    df = df.assign(date_only=base_dt)
    agg = df.groupby(['author', 'date_only']).agg(
        commits=('sha', 'count'),
        lines_added=('additions', 'sum'),
        lines_deleted=('deletions', 'sum'),
        total_changes=('total_changes', 'sum'),
        avg_quality=('quality_score', 'mean'),
        issue_refs=('has_issue_ref', 'sum'),
        conventional_commits=('follows_convention', 'sum'),
        hotfixes=('is_hotfix', 'sum'),
        merges=('is_merge', 'sum'),
        reverts=('is_revert', 'sum'),
        breaking_changes=('has_breaking_change', 'sum'),
    ).reset_index().rename(columns={'author': 'developer', 'date_only': 'date'})

    # Build complete grid of developers x days
    devs = sorted(agg['developer'].unique())
    all_days = pd.date_range(start=start_date.normalize(), end=end_date.normalize(), freq='D')
    idx = _build_complete_index(devs, all_days)
    agg_idxed = agg.set_index(['developer', 'date']).reindex(idx).reset_index()
    agg_idxed = agg_idxed.rename(columns={'level_0': 'developer', 'level_1': 'date'})

    # Fill sums with 0, leave avg_quality NaN when no commits
    sum_cols = ['commits', 'lines_added', 'lines_deleted', 'total_changes', 'issue_refs',
                'conventional_commits', 'hotfixes', 'merges', 'reverts', 'breaking_changes']
    for c in sum_cols:
        agg_idxed[c] = agg_idxed[c].fillna(0).astype(int)

    # Rates and averages
    eps = 1e-9
    agg_idxed['issue_ref_rate'] = (agg_idxed['issue_refs'] / (agg_idxed['commits'] + eps) * 100).round(1)
    agg_idxed['conventional_rate'] = (agg_idxed['conventional_commits'] / (agg_idxed['commits'] + eps) * 100).round(1)
    agg_idxed['hotfix_rate'] = (agg_idxed['hotfixes'] / (agg_idxed['commits'] + eps) * 100).round(1)
    agg_idxed['merge_rate'] = (agg_idxed['merges'] / (agg_idxed['commits'] + eps) * 100).round(1)
    agg_idxed['revert_rate'] = (agg_idxed['reverts'] / (agg_idxed['commits'] + eps) * 100).round(1)
    agg_idxed['breaking_rate'] = (agg_idxed['breaking_changes'] / (agg_idxed['commits'] + eps) * 100).round(1)
    agg_idxed['avg_lines_per_commit'] = (agg_idxed['total_changes'] / (agg_idxed['commits'] + eps)).round(1)

    return agg_idxed


def weekly_timeseries_last_4(commits_df: pd.DataFrame) -> pd.DataFrame:
    """Per-developer weekly series for the last 4 weeks using ISO week starts.
    Columns: week_start, developer, commits, lines_added, lines_deleted, total_changes, avg_quality,
             issue_refs, conventional_commits, hotfixes, merges, reverts, breaking_changes,
             rates similar to daily.
    """
    if commits_df.empty:
        return pd.DataFrame()
    base_dt = commits_df['date_day'] if 'date_day' in commits_df.columns else commits_df['date']
    end_date = base_dt.max()
    start_date = end_date - pd.Timedelta(days=28)
    df = commits_df[base_dt >= start_date].copy()
    if df.empty:
        return pd.DataFrame()
    df = df.assign(week_start=base_dt.dt.to_period('W').dt.start_time)
    agg = df.groupby(['author', 'week_start']).agg(
        commits=('sha', 'count'),
        lines_added=('additions', 'sum'),
        lines_deleted=('deletions', 'sum'),
        total_changes=('total_changes', 'sum'),
        avg_quality=('quality_score', 'mean'),
        issue_refs=('has_issue_ref', 'sum'),
        conventional_commits=('follows_convention', 'sum'),
        hotfixes=('is_hotfix', 'sum'),
        merges=('is_merge', 'sum'),
        reverts=('is_revert', 'sum'),
        breaking_changes=('has_breaking_change', 'sum'),
    ).reset_index().rename(columns={'author': 'developer'})

    # Complete grid: developers x week_starts (cover full 4-week window)
    devs = sorted(agg['developer'].unique())
    # Build week starts from window
    all_weeks = pd.date_range(start=start_date.to_period('W').start_time, end=end_date.to_period('W').start_time, freq='W-MON')
    idx = _build_complete_index(devs, all_weeks)
    agg_idxed = agg.set_index(['developer', 'week_start']).reindex(idx).reset_index()
    agg_idxed = agg_idxed.rename(columns={'level_0': 'developer', 'level_1': 'week_start'})

    sum_cols = ['commits', 'lines_added', 'lines_deleted', 'total_changes', 'issue_refs',
                'conventional_commits', 'hotfixes', 'merges', 'reverts', 'breaking_changes']
    for c in sum_cols:
        agg_idxed[c] = agg_idxed[c].fillna(0).astype(int)

    eps = 1e-9
    agg_idxed['issue_ref_rate'] = (agg_idxed['issue_refs'] / (agg_idxed['commits'] + eps) * 100).round(1)
    agg_idxed['conventional_rate'] = (agg_idxed['conventional_commits'] / (agg_idxed['commits'] + eps) * 100).round(1)
    agg_idxed['hotfix_rate'] = (agg_idxed['hotfixes'] / (agg_idxed['commits'] + eps) * 100).round(1)
    agg_idxed['merge_rate'] = (agg_idxed['merges'] / (agg_idxed['commits'] + eps) * 100).round(1)
    agg_idxed['revert_rate'] = (agg_idxed['reverts'] / (agg_idxed['commits'] + eps) * 100).round(1)
    agg_idxed['breaking_rate'] = (agg_idxed['breaking_changes'] / (agg_idxed['commits'] + eps) * 100).round(1)
    agg_idxed['avg_lines_per_commit'] = (agg_idxed['total_changes'] / (agg_idxed['commits'] + eps)).round(1)

    return agg_idxed


def main():
    commits_csv = config.COMMIT_ANALYSIS_FILE
    out_dir = Path('.')

    commits = load_commits_df(commits_csv)
    commits_core = commits[commits['author'].isin(config.CORE_TEAM)]

    # Last 7 days (same function as dashboard)
    last7 = filter_commits_by_period(commits_core, 'last_7_days')
    stats7 = _aggregate_productivity_from_commits(last7)
    stats7 = stats7.sort_values('total_commits', ascending=False)

    # Last 4 weeks (28 days)
    last4w = filter_last_4_weeks(commits_core)
    stats4w = _aggregate_productivity_from_commits(last4w)
    stats4w = stats4w.sort_values('total_commits', ascending=False)

    # Write CSVs for verification
    stats7.to_csv(out_dir / 'period_stats_last_7_days.csv', index=False)
    stats4w.to_csv(out_dir / 'period_stats_last_4_weeks.csv', index=False)

    # Console summary
    print('=== Period: Last 7 Days ===')
    print(f"Window: {describe_period(last7)} | Developers: {last7['author'].nunique()} | Commits: {len(last7):,}")
    print(stats7.to_string(index=False))
    print('\n=== Period: Last 4 Weeks (28 days) ===')
    print(f"Window: {describe_period(last4w)} | Developers: {last4w['author'].nunique()} | Commits: {len(last4w):,}")
    print(stats4w.to_string(index=False))

    # Time series outputs
    daily7 = daily_timeseries_last_7(commits_core)
    weekly4 = weekly_timeseries_last_4(commits_core)
    if not daily7.empty:
        daily7.to_csv(out_dir / 'timeseries_daily_last_7_days.csv', index=False)
        print(f"\n[written] timeseries_daily_last_7_days.csv rows={len(daily7)}")
    else:
        print("\n[info] No data for daily last 7 days time series")
    if not weekly4.empty:
        weekly4.to_csv(out_dir / 'timeseries_weekly_last_4_weeks.csv', index=False)
        print(f"[written] timeseries_weekly_last_4_weeks.csv rows={len(weekly4)}")
    else:
        print("[info] No data for weekly last 4 weeks time series")


if __name__ == '__main__':
    main()
