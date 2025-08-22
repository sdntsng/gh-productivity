import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.offline as pyo
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np
import config
import json
from pandas.api.types import DatetimeTZDtype

# This script reads commit/productivity CSVs and generates an interactive HTML dashboard
# Run after extract.py has created the CSV files specified in config.py

def create_weekly_trends(commits_df, start_date=None, end_date=None):
    """Create week-on-week trend analysis for developers with optional date filtering.
    Uses a safe copy to avoid chained assignment warnings.
    """
    df = commits_df
    # Filter by date range if provided
    if start_date is not None:
        df = df[df['date'] >= start_date]
    if end_date is not None:
        df = df[df['date'] <= end_date]

    if df.empty:
        return pd.DataFrame()

    df = df.copy()
    # Add week column (normalize to week start)
    df.loc[:, 'week'] = df['date'].dt.to_period('W').dt.start_time

    # Weekly aggregation by developer
    weekly_stats = df.groupby(['author', 'week']).agg({
        'sha': 'count',  # commit count
        'quality_score': 'mean',
        'additions': 'sum',
        'deletions': 'sum',
        'total_changes': 'sum',
        'has_issue_ref': 'sum',
        'follows_convention': 'sum',
        'is_hotfix': 'sum',
        'message_words': 'mean',
        'has_breaking_change': 'sum',
        'is_merge': 'sum',
        'is_revert': 'sum'
    }).reset_index()

    weekly_stats.columns = [
        'developer', 'week', 'commits', 'avg_quality', 'lines_added',
        'lines_deleted', 'total_changes', 'issue_refs', 'conventional_commits', 'hotfixes', 'avg_words',
        'breaking_changes', 'merges', 'reverts'
    ]

    # Calculate percentages
    weekly_stats['conventional_rate'] = (weekly_stats['conventional_commits'] / weekly_stats['commits'] * 100).fillna(0)
    weekly_stats['issue_ref_rate'] = (weekly_stats['issue_refs'] / weekly_stats['commits'] * 100).fillna(0)
    weekly_stats['hotfix_rate'] = (weekly_stats['hotfixes'] / weekly_stats['commits'] * 100).fillna(0)
    weekly_stats['merge_rate'] = (weekly_stats['merges'] / weekly_stats['commits'] * 100).fillna(0)
    weekly_stats['revert_rate'] = (weekly_stats['reverts'] / weekly_stats['commits'] * 100).fillna(0)
    weekly_stats['breaking_rate'] = (weekly_stats['breaking_changes'] / weekly_stats['commits'] * 100).fillna(0)

    return weekly_stats

def filter_commits_by_period(commits_df, period='all'):
    """Filter commits by predefined time periods"""
    if period == 'all':
        return commits_df
    
    end_date = commits_df['date'].max()
    
    if period == 'last_7_days':
        start_date = end_date - timedelta(days=7)
    elif period == 'last_30_days':
        start_date = end_date - timedelta(days=30)
    elif period == 'last_90_days':
        start_date = end_date - timedelta(days=90)
    elif period == 'last_6_months':
        start_date = end_date - timedelta(days=180)
    elif period == 'last_year':
        start_date = end_date - timedelta(days=365)
    elif period == 'current_month':
        start_date = end_date.replace(day=1)
    elif period == 'current_quarter':
        quarter_start_month = ((end_date.month - 1) // 3) * 3 + 1
        start_date = end_date.replace(month=quarter_start_month, day=1)
    else:
        return commits_df
    
    return commits_df[commits_df['date'] >= start_date]

def create_summary_cards(commits_df, prod_df):
    """Create summary statistics cards"""
    total_commits = len(commits_df)
    total_developers = commits_df['author'].nunique()
    total_repos = commits_df['repository'].nunique()
    avg_quality = commits_df['quality_score'].mean()
    total_lines_added = commits_df['additions'].sum()
    total_lines_deleted = commits_df['deletions'].sum()
    
    date_range = f"{commits_df['date'].min().strftime('%Y-%m-%d')} to {commits_df['date'].max().strftime('%Y-%m-%d')}" if not commits_df.empty else 'N/A'
    
    return {
        'total_commits': f"{total_commits:,}",
        'total_developers': total_developers,
        'total_repos': total_repos,
        'avg_quality': f"{avg_quality:.2f}" if not pd.isna(avg_quality) else '0.00',
        'total_lines_added': f"{total_lines_added:,}",
        'total_lines_deleted': f"{total_lines_deleted:,}",
        'date_range': date_range
    }

def _aggregate_productivity_from_commits(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate per-developer productivity stats from raw commits for the selected period.
    Returns columns: developer, total_commits, avg_quality_score, total_lines_added, total_lines_deleted,
    lines_changed, issue_refs, conventional_commits, hotfixes, breaking_changes, merges, reverts,
    and calculated rates.
    """
    if df.empty:
        return pd.DataFrame(
            columns=[
                'developer', 'total_commits', 'avg_quality_score', 'total_lines_added', 'total_lines_deleted',
                'lines_changed', 'issue_refs', 'conventional_commits', 'hotfixes', 'breaking_changes', 'merges', 'reverts',
                'issue_ref_rate', 'conventional_rate', 'hotfix_rate', 'merge_rate', 'revert_rate', 'breaking_rate', 'avg_lines_per_commit'
            ]
        )
    g = df.groupby('author').agg(
        total_commits=('sha', 'count'),
        avg_quality_score=('quality_score', 'mean'),
        total_lines_added=('additions', 'sum'),
        total_lines_deleted=('deletions', 'sum'),
        lines_changed=('total_changes', 'sum'),
        issue_refs=('has_issue_ref', 'sum'),
        conventional_commits=('follows_convention', 'sum'),
        hotfixes=('is_hotfix', 'sum'),
        breaking_changes=('has_breaking_change', 'sum'),
        merges=('is_merge', 'sum'),
        reverts=('is_revert', 'sum')
    ).reset_index().rename(columns={'author': 'developer'})

    # Calculate rates and averages
    g['issue_ref_rate'] = (g['issue_refs'] / g['total_commits'] * 100).round(1).fillna(0)
    g['conventional_rate'] = (g['conventional_commits'] / g['total_commits'] * 100).round(1).fillna(0)
    g['hotfix_rate'] = (g['hotfixes'] / g['total_commits'] * 100).round(1).fillna(0)
    g['merge_rate'] = (g['merges'] / g['total_commits'] * 100).round(1).fillna(0)
    g['revert_rate'] = (g['reverts'] / g['total_commits'] * 100).round(1).fillna(0)
    g['breaking_rate'] = (g['breaking_changes'] / g['total_commits'] * 100).round(1).fillna(0)
    g['avg_lines_per_commit'] = (g['lines_changed'] / g['total_commits']).round(1).fillna(0)

    return g

def _plot_table_from_df(df: pd.DataFrame, title: str) -> go.Figure:
    """Create a Plotly Table figure from a DataFrame with conditional coloring for rates."""
    if df.empty:
        fig = go.Figure()
        fig.update_layout(title=f"{title} - No Data Available")
        return fig
    
    # Round floats for display
    for col in df.select_dtypes(include=['float']).columns:
        df[col] = df[col].round(2)
    
    # Prepare cell colors: white background default
    cell_colors = [['#ffffff'] * len(df) for _ in df.columns]
    
    # Color rate columns: green if >70, yellow 40-70, red <40
    rate_cols = [col for col in df.columns if '_rate' in col]
    for i, col in enumerate(df.columns):
        if col in rate_cols:
            for j, val in enumerate(df[col]):
                if val > 70:
                    cell_colors[i][j] = '#d4edda'  # light green
                elif val > 40:
                    cell_colors[i][j] = '#fff3cd'  # light yellow
                else:
                    cell_colors[i][j] = '#f8d7da'  # light red
    
    header = dict(values=list(df.columns), fill_color='#667eea', align='left', font=dict(color='white', size=12))
    cells = dict(values=[df[col] for col in df.columns], fill_color=cell_colors, align='left')
    fig = go.Figure(data=[go.Table(header=header, cells=cells)])
    fig.update_layout(title=title, height=min(600, 80 + 24 * (len(df) + 1)))
    return fig

def create_enhanced_charts(commits_core, prod_core, weekly_trends):
    """Create enhanced charts with better interactivity and richer stats."""
    charts = {}

    # 0. Compute a period-accurate productivity snapshot
    period_prod = _aggregate_productivity_from_commits(commits_core)

    # 1. Enhanced top performers with hover data (period-correct)
    charts['top_quality'] = px.bar(
        period_prod.sort_values('avg_quality_score', ascending=True),
        x='avg_quality_score',
        y='developer',
        orientation='h',
        title='Top Developers by Average Quality Score',
        hover_data=['total_commits', 'total_lines_added', 'total_lines_deleted', 'avg_lines_per_commit'],
        color='avg_quality_score',
        color_continuous_scale='viridis'
    )
    charts['top_quality'].update_layout(height=400)

    # 2. Volume vs Quality with size by lines changed (period-correct)
    charts['volume_quality'] = px.scatter(
        period_prod,
        x='total_commits',
        y='avg_quality_score',
        size='total_lines_added',
        hover_name='developer',
        title='Commit Volume vs Quality (bubble size = lines added)',
        color='total_lines_deleted',
        color_continuous_scale='reds',
        hover_data=['avg_lines_per_commit', 'hotfix_rate', 'conventional_rate']
    )

    # 3. Weekly commit activity with range selector
    if not weekly_trends.empty:
        charts['weekly_commits'] = px.line(
            weekly_trends,
            x='week',
            y='commits',
            color='developer',
            title='Weekly Commit Activity Trends',
            labels={'commits': 'Commits per Week', 'week': 'Week'}
        )
        charts['weekly_commits'].update_layout(
            xaxis=dict(
                rangeselector=dict(
                    buttons=list([
                        dict(count=1, label="1m", step="month", stepmode="backward"),
                        dict(count=3, label="3m", step="month", stepmode="backward"),
                        dict(count=6, label="6m", step="month", stepmode="backward"),
                        dict(step="all")
                    ])
                ),
                rangeslider=dict(visible=True),
                type="date"
            ),
            hovermode='x unified'
        )
    else:
        charts['weekly_commits'] = go.Figure()
        charts['weekly_commits'].update_layout(title='Weekly Commit Activity Trends - No Data Available')

    # 4. Weekly quality trends
    if not weekly_trends.empty:
        charts['weekly_quality'] = px.line(
            weekly_trends,
            x='week',
            y='avg_quality',
            color='developer',
            title='Weekly Quality Score Trends',
            labels={'avg_quality': 'Average Quality Score', 'week': 'Week'}
        )
        charts['weekly_quality'].update_layout(
            xaxis=dict(type="date", rangeslider=dict(visible=True)),
            hovermode='x unified'
        )
    else:
        charts['weekly_quality'] = go.Figure()
        charts['weekly_quality'].update_layout(title='Weekly Quality Score Trends - No Data Available')

    # 5. Weekly lines changed trends
    if not weekly_trends.empty:
        charts['weekly_changes'] = px.line(
            weekly_trends,
            x='week',
            y='total_changes',
            color='developer',
            title='Weekly Lines Changed Trends',
            labels={'total_changes': 'Total Lines Changed', 'week': 'Week'}
        )
        charts['weekly_changes'].update_layout(
            xaxis=dict(type="date", rangeslider=dict(visible=True)),
            hovermode='x unified'
        )
    else:
        charts['weekly_changes'] = go.Figure()
        charts['weekly_changes'].update_layout(title='Weekly Lines Changed Trends - No Data Available')

    # 6. Weekly conventional rate trends
    if not weekly_trends.empty:
        charts['weekly_conventional'] = px.line(
            weekly_trends,
            x='week',
            y='conventional_rate',
            color='developer',
            title='Weekly Conventional Commit Rate Trends (%)',
            labels={'conventional_rate': 'Conventional Rate (%)', 'week': 'Week'}
        )
        charts['weekly_conventional'].update_layout(
            xaxis=dict(type="date", rangeslider=dict(visible=True)),
            hovermode='x unified'
        )
    else:
        charts['weekly_conventional'] = go.Figure()
        charts['weekly_conventional'].update_layout(title='Weekly Conventional Commit Rate Trends - No Data Available')

    # 7. Daily commits by developer
    if not commits_core.empty:
        _d = commits_core.copy()
        _d.loc[:, 'date_only'] = _d['date'].dt.normalize()
        # Prepare full date range per developer
        date_min = _d['date_only'].min()
        date_max = _d['date_only'].max()
        all_days = pd.date_range(date_min, date_max, freq='D')
        # Count per dev/day
        daily_counts = (_d.groupby(['author', 'date_only']).size()
                          .rename('commits')
                          .reset_index())
        # Reindex per developer to full day range, fill 0
        frames = []
        for dev, g in daily_counts.groupby('author'):
            g2 = g.set_index('date_only').reindex(all_days, fill_value=0)
            g2.index.name = 'date_only'
            g2 = g2.reset_index()
            g2['author'] = dev
            frames.append(g2)
        daily = pd.concat(frames, ignore_index=True)
        daily = daily.rename(columns={'author': 'developer', 'date_only': 'date'})
        charts['daily_by_dev'] = px.bar(
            daily,
            x='date', y='commits', color='developer',
            title='Daily Commits by Developer',
            labels={'commits': 'Commits per Day', 'date': 'Date'}
        )
        charts['daily_by_dev'].update_layout(
            barmode='group',
            xaxis=dict(
                rangeselector=dict(
                    buttons=list([
                        dict(count=7, label="7d", step="day", stepmode="backward"),
                        dict(count=1, label="1m", step="month", stepmode="backward"),
                        dict(count=3, label="3m", step="month", stepmode="backward"),
                        dict(step="all")
                    ])
                ),
                rangeslider=dict(visible=True),
                type="date"
            ),
            hovermode='x unified'
        )
    else:
        charts['daily_by_dev'] = go.Figure()
        charts['daily_by_dev'].update_layout(title='Daily Commits by Developer - No Data Available')

    # 8. Repository activity heatmap (Top 10 repos)
    repo_daily = commits_core.groupby([commits_core['date'].dt.date.rename('date'), 'repository']).size().reset_index(name='commits')
    top_repos = commits_core['repository'].value_counts().head(10).index.tolist()
    repo_daily_top = repo_daily[repo_daily['repository'].isin(top_repos)]
    if not repo_daily_top.empty:
        charts['repo_heatmap'] = px.density_heatmap(
            repo_daily_top,
            x='date',
            y='repository',
            z='commits',
            title='Repository Activity Heatmap (Top 10 Most Active)',
            color_continuous_scale='blues'
        )
    else:
        charts['repo_heatmap'] = go.Figure()
        charts['repo_heatmap'].update_layout(title='Repository Activity Heatmap - No Data Available')

    # 9. Commit timing patterns
    _commits = commits_core.copy()
    _commits.loc[:, 'hour'] = _commits['date'].dt.hour
    _commits.loc[:, 'day_of_week'] = _commits['date'].dt.day_name()
    timing_data = _commits.groupby(['hour', 'day_of_week']).size().reset_index(name='commits')
    if not timing_data.empty:
        charts['timing_heatmap'] = px.density_heatmap(
            timing_data,
            x='hour',
            y='day_of_week',
            z='commits',
            title='Commit Timing Patterns (Hour vs Day of Week)',
            labels={'hour': 'Hour of Day', 'day_of_week': 'Day of Week'},
            color_continuous_scale='viridis'
        )
    else:
        charts['timing_heatmap'] = go.Figure()
        charts['timing_heatmap'].update_layout(title='Commit Timing Patterns - No Data Available')

    # 10. Commit types distribution pie
    if not commits_core.empty:
        types_counts = {
            'Merges': commits_core['is_merge'].sum(),
            'Reverts': commits_core['is_revert'].sum(),
            'Hotfixes': commits_core['is_hotfix'].sum(),
            'Breaking Changes': commits_core['has_breaking_change'].sum(),
            'Regular': len(commits_core) - commits_core[['is_merge', 'is_revert', 'is_hotfix']].any(axis=1).sum()
        }
        types_df = pd.DataFrame({'Type': list(types_counts.keys()), 'Count': list(types_counts.values())})
        types_df = types_df[types_df['Count'] > 0]
        charts['commit_types'] = px.pie(
            types_df,
            values='Count',
            names='Type',
            title='Commit Types Distribution',
            color_discrete_sequence=px.colors.qualitative.Set2
        )
    else:
        charts['commit_types'] = go.Figure()
        charts['commit_types'].update_layout(title='Commit Types Distribution - No Data Available')

    # 11. Developer summary table (period) with rates
    dev_table_df = period_prod[['developer', 'total_commits', 'avg_quality_score', 'total_lines_added', 
                                'total_lines_deleted', 'lines_changed', 'avg_lines_per_commit', 
                                'issue_ref_rate', 'conventional_rate', 'hotfix_rate', 'merge_rate', 
                                'revert_rate', 'breaking_rate', 'breaking_changes']]
    dev_table_df = dev_table_df.sort_values('total_commits', ascending=False)
    charts['developer_summary_table'] = _plot_table_from_df(dev_table_df, 'Developer Performance Summary')

    # 12. Repository leaderboard table (period)
    repo_leader = commits_core.groupby('repository').agg(
        commits=('sha', 'count'),
        developers=('author', 'nunique'),
        avg_quality=('quality_score', 'mean'),
        lines_added=('additions', 'sum'),
        lines_deleted=('deletions', 'sum'),
        lines_changed=('total_changes', 'sum'),
        avg_lines_per_commit=('total_changes', 'mean'),
        hotfixes=('is_hotfix', 'sum'),
        breaking_changes=('has_breaking_change', 'sum')
    ).reset_index().sort_values('commits', ascending=False)
    charts['repo_leaderboard'] = _plot_table_from_df(repo_leader.head(15), 'Top Repositories Leaderboard')

    return charts

def create_dashboard_html():
    """Create the base HTML template for the dashboard"""
    return '''<!DOCTYPE html>
<html>
<head>
    <title>GitHub Productivity Analytics Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background-color: #f8f9fa;
        }
        .header { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; 
            padding: 30px; 
            border-radius: 10px; 
            margin-bottom: 30px;
            text-align: center;
        }
        .tabs {
            display: flex;
            background: white;
            border-radius: 10px;
            padding: 5px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            flex-wrap: wrap;
        }
        .tab-button {
            flex: 1;
            padding: 15px 20px;
            border: none;
            background: transparent;
            cursor: pointer;
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.3s ease;
            min-width: 120px;
        }
        .tab-button.active {
            background: #667eea;
            color: white;
        }
        .tab-button:hover {
            background: #e9ecef;
        }
        .tab-button.active:hover {
            background: #5a6fd8;
        }
        .tab-content {
            display: none;
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .tab-content.active {
            display: block;
        }
        .summary-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .summary-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
            border-left: 4px solid #667eea;
        }
        .summary-card .value {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
            display: block;
        }
        .summary-card .label {
            color: #6c757d;
            margin-top: 5px;
            font-size: 0.9em;
        }
        .chart-container {
            background: white;
            margin-bottom: 30px;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .grid-2 {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        .grid-3 {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
        }
        .filters {
            background: white;
            border-radius: 10px;
            padding: 12px 16px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.06);
            margin-bottom: 16px;
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 12px;
        }
        .filters label {
            font-size: 0.9em;
            color: #495057;
            margin-right: 8px;
        }
        .chip-group {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }
        .chip {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: #f1f3f5;
            border-radius: 999px;
            padding: 6px 10px;
            font-size: 0.85em;
        }
        .chip input {
            accent-color: #667eea;
        }
        @media (max-width: 1200px) {
            .grid-3 { grid-template-columns: 1fr 1fr; }
        }
        @media (max-width: 768px) {
            .grid-2, .grid-3 { grid-template-columns: 1fr; }
            .tabs { flex-direction: column; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>GitHub Productivity Analytics Dashboard</h1>
        <p>Interactive insights into developer productivity and team performance</p>
        <p><small>Generated: {generation_time}</small></p>
    </div>
    
    <div class="tabs">
        {tab_buttons}
    </div>
    
    {tab_contents}
    
    <script>
    function openTab(evt, tabName) {
        var i, tabcontent, tablinks;
        tabcontent = document.getElementsByClassName("tab-content");
        for (i = 0; i < tabcontent.length; i++) {
            tabcontent[i].classList.remove("active");
        }
        tablinks = document.getElementsByClassName("tab-button");
        for (i = 0; i < tablinks.length; i++) {
            tablinks[i].classList.remove("active");
        }
        document.getElementById(tabName).classList.add("active");
        evt.currentTarget.classList.add("active");
        
        // Trigger Plotly relayout to handle responsive charts
        setTimeout(function() {
            window.dispatchEvent(new Event('resize'));
        }, 100);

        // Initialize developer filters on first activation
        if (!window._devFilterInit) { window._devFilterInit = new Set(); }
        if (!window._devFilterInit.has(tabName)) {
            try { initDeveloperFilters(tabName); } catch (e) { console.warn(e); }
            window._devFilterInit.add(tabName);
        }
    }
    
    // Make charts responsive
    window.addEventListener('resize', function() {
        var plotElements = document.querySelectorAll('.plotly-graph-div');
        plotElements.forEach(function(element) {
            if (element.style.display !== 'none') {
                Plotly.Plots.resize(element);
            }
        });
    });

    function initDeveloperFilters(tabId) {
        var dailyId = tabId + '-daily-by-dev';
        var dailyEl = document.getElementById(dailyId);
        if (!dailyEl || !dailyEl.data) return;
        var names = Array.from(new Set((dailyEl.data || []).map(t => t.name).filter(Boolean)));
        var container = document.getElementById(tabId + '-dev-filters');
        if (!container) return;
        container.innerHTML = '';
        names.forEach(function(name) {
            var chip = document.createElement('label');
            chip.className = 'chip';
            var cb = document.createElement('input');
            cb.type = 'checkbox';
            cb.value = name;
            cb.checked = true;
            cb.addEventListener('change', function() { applyDeveloperFilter(tabId); });
            chip.appendChild(cb);
            var txt = document.createElement('span');
            txt.textContent = name;
            chip.appendChild(txt);
            container.appendChild(chip);
        });
    }

    function getSelectedDevelopers(tabId) {
        var container = document.getElementById(tabId + '-dev-filters');
        if (!container) return [];
        var cbs = container.querySelectorAll('input[type="checkbox"]');
        var selected = [];
        cbs.forEach(function(cb) { if (cb.checked) selected.push(cb.value); });
        return selected;
    }

    function applyDeveloperFilter(tabId) {
        var selected = new Set(getSelectedDevelopers(tabId));
        var chartIds = [
            tabId + '-daily-by-dev', 
            tabId + '-weekly-commits', 
            tabId + '-weekly-quality', 
            tabId + '-weekly-changes', 
            tabId + '-weekly-conventional'
        ];
        chartIds.forEach(function(cid) {
            var el = document.getElementById(cid);
            if (!el || !el.data) return;
            var vis = (el.data || []).map(t => selected.has(t.name) ? true : 'legendonly');
            vis.forEach(function(v, idx) {
                try { Plotly.restyle(el, {visible: v}, [idx]); } catch (e) {}
            });
        });
    }

    // Initialize first tab filters on load
    window.addEventListener('load', function() {
        var active = document.querySelector('.tab-content.active');
        if (active && active.id) {
            try { initDeveloperFilters(active.id); } catch (e) { console.warn(e); }
        }
    });
    </script>
</body>
</html>'''

def main(commits_csv: str = None, prod_csv: str = None, out_html: str = None):
    # Use config defaults if not specified
    commits_csv = commits_csv or config.COMMIT_ANALYSIS_FILE
    prod_csv = prod_csv or config.PRODUCTIVITY_FILE
    out_html = out_html or config.DASHBOARD_FILE
    
    commits = pd.read_csv(commits_csv, parse_dates=['date'])
    
    # Convert boolean string columns to integers
    bool_cols = ['has_issue_ref', 'follows_convention', 'is_merge', 'is_revert', 'is_hotfix', 'has_breaking_change']
    for col in bool_cols:
        commits[col] = commits[col].map({'TRUE': 1, 'FALSE': 0}).fillna(0).astype(int)
    
    # Normalize timezone to avoid pandas warnings in period conversions
    try:
        if isinstance(commits['date'].dtype, DatetimeTZDtype):
            if commits['date'].dt.tz is not None:
                commits['date'] = commits['date'].dt.tz_convert('UTC').dt.tz_localize(None)
            else:
                commits['date'] = commits['date'].dt.tz_localize(None)
    except Exception:
        # Fallback: best-effort drop tz if present
        try:
            commits['date'] = commits['date'].dt.tz_localize(None)
        except Exception:
            pass
    prod = pd.read_csv(prod_csv)
    
    # Filter to core team only (exclude external contributors)
    commits_core = commits[commits['author'].isin(config.CORE_TEAM)]
    prod_core = prod[prod['developer'].isin(config.CORE_TEAM)]

    # Create multiple time period views
    time_periods = {
        'all': 'All Time',
        'last_30_days': 'Last 30 Days', 
        'last_90_days': 'Last 90 Days',
        'last_6_months': 'Last 6 Months',
        'current_month': 'Current Month',
        'current_quarter': 'Current Quarter'
    }
    
    # Generate tab buttons
    tab_buttons = []
    for i, (period, label) in enumerate(time_periods.items()):
        active_class = " active" if i == 0 else ""
        tab_buttons.append(f'<button class="tab-button{active_class}" onclick="openTab(event, \'{period}\')">{label}</button>')
    
    # Generate tab contents
    tab_contents = []
    
    for i, (period, label) in enumerate(time_periods.items()):
        # Filter data for this time period
        period_commits = filter_commits_by_period(commits_core, period)
        
        # Create weekly trends for this period
        weekly_trends = create_weekly_trends(period_commits)
        
        # Compute period productivity snapshot from commits (ensures period-correct tables/charts)
        period_prod = _aggregate_productivity_from_commits(period_commits)
        
        # Create summary cards (handle empty safely)
        summary = create_summary_cards(period_commits, period_prod)
        
        # Create enhanced charts
        charts = create_enhanced_charts(period_commits, period_prod, weekly_trends)
        
        # Build tab content
        active_class = " active" if i == 0 else ""
        
        tab_content = f'''
        <div id="{period}" class="tab-content{active_class}">
            <h2>{label} Overview</h2>
            
            <div class="summary-cards">
                <div class="summary-card"><span class="value">{summary["total_commits"]}</span><div class="label">Total Commits</div></div>
                <div class="summary-card"><span class="value">{summary["total_developers"]}</span><div class="label">Active Developers</div></div>
                <div class="summary-card"><span class="value">{summary["total_repos"]}</span><div class="label">Repositories</div></div>
                <div class="summary-card"><span class="value">{summary["avg_quality"]}</span><div class="label">Avg Quality Score</div></div>
                <div class="summary-card"><span class="value">{summary["total_lines_added"]}</span><div class="label">Lines Added</div></div>
                <div class="summary-card"><span class="value">{summary["total_lines_deleted"]}</span><div class="label">Lines Deleted</div></div>
            </div>
            
            <p><strong>Period:</strong> {summary["date_range"]}</p>
            
            <div class="filters">
                <label>Developers:</label>
                <div id="{period}-dev-filters" class="chip-group"></div>
            </div>
            
            <div class="chart-container">
                {charts['weekly_commits'].to_html(full_html=False, include_plotlyjs=False, div_id=f"{period}-weekly-commits")}
            </div>
            
            <div class="chart-container">
                {charts['daily_by_dev'].to_html(full_html=False, include_plotlyjs=False, div_id=f"{period}-daily-by-dev")}
            </div>
            
            <div class="grid-3">
                <div class="chart-container">
                    {charts['weekly_quality'].to_html(full_html=False, include_plotlyjs=False, div_id=f"{period}-weekly-quality")}
                </div>
                <div class="chart-container">
                    {charts['weekly_changes'].to_html(full_html=False, include_plotlyjs=False, div_id=f"{period}-weekly-changes")}
                </div>
                <div class="chart-container">
                    {charts['weekly_conventional'].to_html(full_html=False, include_plotlyjs=False, div_id=f"{period}-weekly-conventional")}
                </div>
            </div>
            
            <div class="grid-2">
                <div class="chart-container">
                    {charts['top_quality'].to_html(full_html=False, include_plotlyjs=False)}
                </div>
                <div class="chart-container">
                    {charts['volume_quality'].to_html(full_html=False, include_plotlyjs=False)}
                </div>
            </div>
            
            <div class="grid-2">
                <div class="chart-container">
                    {charts['repo_heatmap'].to_html(full_html=False, include_plotlyjs=False)}
                </div>
                <div class="chart-container">
                    {charts['timing_heatmap'].to_html(full_html=False, include_plotlyjs=False)}
                </div>
            </div>
            
            <div class="chart-container">
                {charts['commit_types'].to_html(full_html=False, include_plotlyjs=False)}
            </div>

            <div class="grid-2">
                <div class="chart-container">
                    {charts['developer_summary_table'].to_html(full_html=False, include_plotlyjs=False)}
                </div>
                <div class="chart-container">
                    {charts['repo_leaderboard'].to_html(full_html=False, include_plotlyjs=False)}
                </div>
            </div>
            
            <div class="feedback-section">
                <h3>Developer Feedback Suggestions</h3>
                <p>Use this dashboard to compare your metrics against team averages. Aim for higher conventional commit rates (>80%) and lower hotfix/revert rates (<5%). Discuss improvements in team meetings.</p>
            </div>
        </div>
        '''
        
        tab_contents.append(tab_content)
    
    # Create the complete HTML
    html_template = create_dashboard_html()
    html = html_template.format(
        generation_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        tab_buttons=''.join(tab_buttons),
        tab_contents=''.join(tab_contents)
    )
    
    # Write the complete HTML
    Path(out_html).write_text(html, encoding='utf-8')
    
    print(f"Enhanced interactive dashboard written to {out_html}")
    print(f"Features:")
    print(f"  ✅ Time period selection ({len(time_periods)} periods)")
    print(f"  ✅ Interactive charts with zoom, pan, and filters")
    print(f"  ✅ Summary statistics for each period")
    print(f"  ✅ Additional trend charts for quality, changes, conventional rates")
    print(f"  ✅ Commit types distribution")
    print(f"  ✅ Enhanced tables with rates, averages, and conditional coloring")
    print(f"  ✅ Repository leaderboard with more metrics")
    print(f"  ✅ Developer feedback section")
    print(f"  ✅ Responsive design for mobile devices")
    print(f"  ✅ Professional UI with gradient headers")
    print(f"\nAnalysis covers {commits_core['repository'].nunique()} repositories and {len(commits_core):,} commits from core team")

if __name__ == '__main__':
    main()