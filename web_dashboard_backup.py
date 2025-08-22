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

# This script reads commit/productivity CSVs and generates an interactive HTML dashboard
# Run after extract.py has created the CSV files specified in config.py

def create_weekly_trends(commits_df, start_date=None, end_date=None):
    """Create week-on-week trend analysis for developers with optional date filtering"""
    # Filter by date range if provided
    if start_date:
        commits_df = commits_df[commits_df['date'] >= start_date]
    if end_date:
        commits_df = commits_df[commits_df['date'] <= end_date]
    
    if commits_df.empty:
        return pd.DataFrame()
    
    # Add week column
    commits_df['week'] = commits_df['date'].dt.to_period('W').dt.start_time
    
    # Weekly aggregation by developer
    weekly_stats = commits_df.groupby(['author', 'week']).agg({
        'sha': 'count',  # commit count
        'quality_score': 'mean',
        'additions': 'sum',
        'deletions': 'sum', 
        'total_changes': 'sum',
        'has_issue_ref': 'sum',
        'follows_convention': 'sum',
        'is_hotfix': 'sum',
        'message_words': 'mean'
    }).reset_index()
    
    weekly_stats.columns = ['developer', 'week', 'commits', 'avg_quality', 'lines_added', 
                           'lines_deleted', 'total_changes', 'issue_refs', 'conventional_commits', 'hotfixes', 'avg_words']
    
    # Calculate percentages
    weekly_stats['conventional_rate'] = (weekly_stats['conventional_commits'] / weekly_stats['commits'] * 100).fillna(0)
    weekly_stats['issue_ref_rate'] = (weekly_stats['issue_refs'] / weekly_stats['commits'] * 100).fillna(0)
    weekly_stats['hotfix_rate'] = (weekly_stats['hotfixes'] / weekly_stats['commits'] * 100).fillna(0)
    
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
    
    date_range = f"{commits_df['date'].min().strftime('%Y-%m-%d')} to {commits_df['date'].max().strftime('%Y-%m-%d')}"
    
    return {
        'total_commits': f"{total_commits:,}",
        'total_developers': total_developers,
        'total_repos': total_repos,
        'avg_quality': f"{avg_quality:.2f}",
        'total_lines_added': f"{total_lines_added:,}",
        'total_lines_deleted': f"{total_lines_deleted:,}",
        'date_range': date_range
    }

def create_enhanced_charts(commits_core, prod_core, weekly_trends):
    """Create enhanced charts with better interactivity"""
    charts = {}
    
    # 1. Enhanced top performers with hover data
    charts['top_quality'] = px.bar(
        prod_core, 
        x='avg_quality_score', 
        y='developer', 
        orientation='h',
        title='Top Developers by Average Quality Score',
        hover_data=['total_commits', 'total_lines_added', 'total_lines_deleted'],
        color='avg_quality_score',
        color_continuous_scale='viridis'
    )
    charts['top_quality'].update_layout(height=400)
    
    # 2. Volume vs Quality with size by lines changed
    charts['volume_quality'] = px.scatter(
        prod_core, 
        x='total_commits', 
        y='avg_quality_score',
        size='total_lines_added',
        hover_name='developer',
        title='Commit Volume vs Quality (bubble size = lines added)',
        color='total_lines_deleted',
        color_continuous_scale='reds'
    )
    
    # 3. Weekly commit activity with range selector
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
    
    # 4. Repository activity heatmap
    repo_daily = commits_core.groupby([commits_core['date'].dt.date, 'repository']).size().reset_index(name='commits')
    top_repos = commits_core['repository'].value_counts().head(10).index.tolist()
    repo_daily_top = repo_daily[repo_daily['repository'].isin(top_repos)]
    
    charts['repo_heatmap'] = px.density_heatmap(
        repo_daily_top,
        x='date',
        y='repository', 
        z='commits',
        title='Repository Activity Heatmap (Top 10 Most Active)',
        color_continuous_scale='blues'
    )
    
    # 5. Commit timing patterns
    commits_core['hour'] = commits_core['date'].dt.hour
    commits_core['day_of_week'] = commits_core['date'].dt.day_name()
    
    timing_data = commits_core.groupby(['hour', 'day_of_week']).size().reset_index(name='commits')
    
    charts['timing_heatmap'] = px.density_heatmap(
        timing_data,
        x='hour',
        y='day_of_week',
        z='commits',
        title='Commit Timing Patterns (Hour vs Day of Week)',
        labels={'hour': 'Hour of Day', 'day_of_week': 'Day of Week'},
        color_continuous_scale='viridis'
    )
    
    return charts

def main(commits_csv: str = None, prod_csv: str = None, out_html: str = None):
    # Use config defaults if not specified
    commits_csv = commits_csv or config.COMMIT_ANALYSIS_FILE
    prod_csv = prod_csv or config.PRODUCTIVITY_FILE
    out_html = out_html or config.DASHBOARD_FILE
    
    commits = pd.read_csv(commits_csv, parse_dates=['date'])
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
    
    # Generate dashboard HTML with tabbed interface
    html_parts = [
        """
        <!DOCTYPE html>
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
                @media (max-width: 768px) {
                    .grid-2 { grid-template-columns: 1fr; }
                    .tabs { flex-direction: column; }
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>GitHub Productivity Analytics Dashboard</h1>
                <p>Interactive insights into developer productivity and team performance</p>
            </div>
            
            <div class="tabs">
        ",
        
        # Add tab buttons
        ''.join([f'<button class="tab-button{
    
    # === EXISTING CHARTS ===
    # Top performers by quality
    fig_top_quality = px.bar(prod_core, x='avg_quality_score', y='developer', orientation='h', 
                            title='Top Developers by Avg Quality Score (Core Team)')

    # Commit volume vs quality scatter
    fig_volume_quality = px.scatter(prod_core, x='total_commits', y='avg_quality_score', 
                                   hover_data=['developer'], title='Commit Volume vs Quality (Core Team)')

    # === NEW WEEKLY TREND CHARTS ===
    
    # 1. Weekly commit activity
    fig_weekly_commits = px.line(weekly_trends, x='week', y='commits', color='developer',
                                title='Weekly Commit Activity Trends',
                                labels={'commits': 'Commits per Week', 'week': 'Week'})
    fig_weekly_commits.update_layout(hovermode='x unified')
    
    # 2. Weekly quality trends  
    fig_weekly_quality = px.line(weekly_trends, x='week', y='avg_quality', color='developer',
                                title='Weekly Quality Score Trends',
                                labels={'avg_quality': 'Average Quality Score', 'week': 'Week'})
    fig_weekly_quality.update_layout(hovermode='x unified')
    
    # 3. Weekly lines of code trends
    fig_weekly_loc = px.line(weekly_trends, x='week', y='total_changes', color='developer',
                            title='Weekly Lines of Code Changed',
                            labels={'total_changes': 'Total Lines Changed', 'week': 'Week'})
    fig_weekly_loc.update_layout(hovermode='x unified')
    
    # 4. Weekly conventional commits adoption
    fig_weekly_conv = px.line(weekly_trends, x='week', y='conventional_rate', color='developer',
                             title='Weekly Conventional Commits Adoption Rate (%)',
                             labels={'conventional_rate': 'Conventional Commits %', 'week': 'Week'})
    fig_weekly_conv.update_layout(hovermode='x unified')
    
    # 5. Multi-metric dashboard for each developer
    fig_multi_metrics = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Commits per Week', 'Quality Score', 'Lines Changed', 'Issue Reference Rate'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    colors = px.colors.qualitative.Set1[:len(config.CORE_TEAM)]
    for i, dev in enumerate(config.CORE_TEAM):
        dev_data = weekly_trends[weekly_trends['developer'] == dev]
        
        # Commits
        fig_multi_metrics.add_trace(
            go.Scatter(x=dev_data['week'], y=dev_data['commits'], name=f'{dev} Commits',
                      line=dict(color=colors[i]), showlegend=(i==0)),
            row=1, col=1
        )
        
        # Quality
        fig_multi_metrics.add_trace(
            go.Scatter(x=dev_data['week'], y=dev_data['avg_quality'], name=f'{dev} Quality',
                      line=dict(color=colors[i]), showlegend=False),
            row=1, col=2
        )
        
        # Lines changed
        fig_multi_metrics.add_trace(
            go.Scatter(x=dev_data['week'], y=dev_data['total_changes'], name=f'{dev} Lines',
                      line=dict(color=colors[i]), showlegend=False),
            row=2, col=1
        )
        
        # Issue ref rate
        fig_multi_metrics.add_trace(
            go.Scatter(x=dev_data['week'], y=dev_data['issue_ref_rate'], name=f'{dev} Issue Refs',
                      line=dict(color=colors[i]), showlegend=False),
            row=2, col=2
        )
    
    fig_multi_metrics.update_layout(
        title_text="Developer Performance Metrics - Weekly Trends",
        height=600,
        hovermode='x unified'
    )
    
    # 6. Repository activity heatmap
    repo_weekly = commits_core.groupby([commits_core['date'].dt.to_period('W').dt.start_time, 'repository']).size().reset_index(name='commits')
    repo_weekly['week'] = repo_weekly['date']
    
    # Top 10 most active repos
    top_repos = commits_core['repository'].value_counts().head(10).index.tolist()
    repo_weekly_top = repo_weekly[repo_weekly['repository'].isin(top_repos)]
    
    fig_repo_heatmap = px.line(repo_weekly_top, x='week', y='commits', color='repository',
                              title='Weekly Repository Activity (Top 10 Most Active)',
                              labels={'commits': 'Commits per Week', 'week': 'Week'})
    fig_repo_heatmap.update_layout(hovermode='x unified')

    # === ENHANCED OVERVIEW CHARTS ===
    # Lines of code overview
    fig_lines_overview = px.bar(prod_core, x='developer', y=['total_lines_added', 'total_lines_deleted'],
                               title='Total Lines Added vs Deleted by Developer',
                               barmode='group')
    
    # Time-based working patterns
    commits_core['commit_hour'] = commits_core['date'].dt.hour
    hourly_commits = commits_core.groupby(['author', 'commit_hour']).size().reset_index(name='commits')
    fig_working_hours = px.line(hourly_commits, x='commit_hour', y='commits', color='author',
                               title='Developer Working Hours Pattern (Commits by Hour of Day)',
                               labels={'commit_hour': 'Hour of Day (24h)', 'commits': 'Number of Commits'})

    # Assemble all figures into a comprehensive HTML dashboard
    html_parts = [
        f"<h1>🚀 Developer Productivity Dashboard - Enhanced Analytics</h1>",
        f"<p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')} | <strong>Core Team Analysis</strong></p>",
        f"<p><strong>Analysis Period:</strong> {commits_core['date'].min().strftime('%Y-%m-%d')} to {commits_core['date'].max().strftime('%Y-%m-%d')}</p>",
        f"<p><strong>Total Repositories:</strong> {commits_core['repository'].nunique()} | <strong>Total Commits:</strong> {len(commits_core):,}</p>",
        
        "<h2>📊 Weekly Trends & Performance Analysis</h2>",
        fig_multi_metrics.to_html(full_html=False, include_plotlyjs='cdn'),
        
        "<h2>📈 Individual Metric Trends</h2>",
        fig_weekly_commits.to_html(full_html=False, include_plotlyjs=False),
        fig_weekly_quality.to_html(full_html=False, include_plotlyjs=False),
        fig_weekly_loc.to_html(full_html=False, include_plotlyjs=False),
        fig_weekly_conv.to_html(full_html=False, include_plotlyjs=False),
        
        "<h2>🏆 Overall Performance Comparison</h2>",
        fig_top_quality.to_html(full_html=False, include_plotlyjs=False),
        fig_volume_quality.to_html(full_html=False, include_plotlyjs=False),
        fig_lines_overview.to_html(full_html=False, include_plotlyjs=False),
        
        "<h2>🕒 Working Patterns & Repository Activity</h2>",
        fig_working_hours.to_html(full_html=False, include_plotlyjs=False),
        fig_repo_heatmap.to_html(full_html=False, include_plotlyjs=False),
        
        "<hr><p><em>Dashboard shows core team members only. External contributors and bots excluded for clarity.</em></p>"
    ]
    
    html = "\n".join(html_parts)
    Path(out_html).write_text(html, encoding='utf-8')
    print(f"Enhanced dashboard written to {out_html}")
    print(f"Analysis covers {commits_core['repository'].nunique()} repositories and {len(commits_core):,} commits from core team")

if __name__ == '__main__':
    main()
