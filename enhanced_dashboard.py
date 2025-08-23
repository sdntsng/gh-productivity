import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.offline as pyo
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np
import asyncio
from typing import Dict, List, Any
import config
from llm_analyzer import LLMCommitAnalyzer, DeveloperSummaryGenerator, CommitAnalysis, DeveloperPeriodSummary

class EnhancedDashboardGenerator:
    """Generate enhanced dashboard with LLM-powered insights and comparative analytics"""
    
    def __init__(self):
        self.llm_analyzer = LLMCommitAnalyzer()
        self.summary_generator = DeveloperSummaryGenerator(self.llm_analyzer)
        
    async def create_enhanced_dashboard(self, commits_csv: str = None, out_html: str = None):
        """Create enhanced dashboard with LLM insights and comparative metrics"""
        
        # Load data
        commits_csv = commits_csv or config.COMMIT_ANALYSIS_FILE
        out_html = out_html or "enhanced_dashboard.html"
        
        print("Loading commit data...")
        commits_df = self._load_and_prepare_data(commits_csv)
        
        # Perform LLM analysis if enabled
        if config.ENABLE_LLM_ANALYSIS and config.GEMINI_API_KEY:
            print("Performing LLM analysis...")
            enhanced_analyses = await self._perform_llm_analysis(commits_df)
            commits_df = self._merge_llm_insights(commits_df, enhanced_analyses)
        
        # Generate developer summaries
        print("Generating developer summaries...")
        developer_summaries = self._generate_developer_summaries(commits_df)
        
        # Create enhanced visualizations
        print("Creating enhanced visualizations...")
        dashboard_data = self._create_enhanced_dashboard_data(commits_df, developer_summaries)
        
        # Generate HTML dashboard
        print("Generating HTML dashboard...")
        html_content = self._create_enhanced_html(dashboard_data)
        
        # Write dashboard
        Path(out_html).write_text(html_content, encoding='utf-8')
        print(f"Enhanced dashboard created: {out_html}")
        
        return dashboard_data
    
    def _load_and_prepare_data(self, commits_csv: str) -> pd.DataFrame:
        """Load and prepare commit data"""
        df = pd.read_csv(commits_csv, parse_dates=['date'])
        
        # Convert boolean strings to integers
        bool_cols = ['has_issue_ref', 'follows_convention', 'is_merge', 'is_revert', 'is_hotfix', 'has_breaking_change']
        for col in bool_cols:
            if col in df.columns:
                df[col] = df[col].map({'TRUE': 1, 'FALSE': 0}).fillna(0).astype(int)
        
        # Normalize timezone
        try:
            df['date'] = pd.to_datetime(df['date'], utc=True).dt.tz_localize(None)
        except:
            pass
        
        # Filter to core team
        if hasattr(config, 'CORE_TEAM'):
            df = df[df['author'].isin(config.CORE_TEAM)].copy()
        
        return df
    
    async def _perform_llm_analysis(self, commits_df: pd.DataFrame) -> List[CommitAnalysis]:
        """Perform LLM analysis on commits"""
        commits_data = []
        
        for _, row in commits_df.iterrows():
            commit_data = {
                'sha': row['sha'],
                'author': row['author'],
                'repository': row['repository'],
                'date': row['date'].isoformat(),
                'message': row['message'],
                'quality_score': row.get('quality_score', 5.0),
                'additions': row.get('additions', 0),
                'deletions': row.get('deletions', 0),
                'total_changes': row.get('total_changes', 0),
                'files_changed': row.get('files_changed', ''),
                'diff': ''  # Would need to fetch from git API
            }
            commits_data.append(commit_data)
        
        # Process in batches
        batch_size = config.LLM_BATCH_SIZE
        all_analyses = []
        
        for i in range(0, len(commits_data), batch_size):
            batch = commits_data[i:i + batch_size]
            batch_analyses = await self.llm_analyzer.analyze_commits_batch(batch)
            all_analyses.extend(batch_analyses)
        
        return all_analyses
    
    def _merge_llm_insights(self, commits_df: pd.DataFrame, analyses: List[CommitAnalysis]) -> pd.DataFrame:
        """Merge LLM insights back into commits dataframe"""
        df = commits_df.copy()
        
        # Create lookup dict
        analysis_dict = {a.sha: a for a in analyses}
        
        # Add LLM columns
        llm_cols = ['llm_quality_score', 'business_impact_score', 'feature_type', 
                   'complexity_level', 'risk_level']
        
        for col in llm_cols:
            df[col] = df['sha'].map(lambda sha: getattr(analysis_dict.get(sha), col, None))
        
        return df
    
    def _generate_developer_summaries(self, commits_df: pd.DataFrame) -> List[DeveloperPeriodSummary]:
        """Generate developer performance summaries"""
        # Create CommitAnalysis objects from DataFrame
        analyses = []
        for _, row in commits_df.iterrows():
            analysis = CommitAnalysis(
                sha=row['sha'],
                author=row['author'],
                repository=row['repository'],
                date=row['date'].isoformat(),
                message=row['message'],
                quality_score=row.get('quality_score', 5.0),
                additions=row.get('additions', 0),
                deletions=row.get('deletions', 0),
                total_changes=row.get('total_changes', 0),
                llm_quality_score=row.get('llm_quality_score', 0.0),
                business_impact_score=row.get('business_impact_score', 0.0),
                feature_type=row.get('feature_type', 'maintenance'),
                complexity_level=row.get('complexity_level', 'medium'),
                risk_level=row.get('risk_level', 'low')
            )
            analyses.append(analysis)
        
        # Generate weekly summaries
        return self.summary_generator.generate_period_summaries(analyses, period_days=7)
    
    def _create_enhanced_dashboard_data(self, commits_df: pd.DataFrame, summaries: List[DeveloperPeriodSummary]) -> Dict:
        """Create enhanced dashboard data with comparative metrics"""
        
        # Core metrics
        dashboard_data = {
            'commits_df': commits_df,
            'summaries': summaries,
            'charts': {},
            'summary_stats': self._calculate_summary_stats(commits_df),
            'comparative_metrics': self._calculate_comparative_metrics(commits_df),
            'developer_rankings': self._calculate_developer_rankings(commits_df),
            'time_series_data': self._create_time_series_data(commits_df)
        }
        
        # Create enhanced charts
        dashboard_data['charts'] = self._create_enhanced_charts(commits_df, summaries)
        
        return dashboard_data
    
    def _calculate_summary_stats(self, df: pd.DataFrame) -> Dict:
        """Calculate enhanced summary statistics"""
        return {
            'total_commits': len(df),
            'total_developers': df['author'].nunique(),
            'total_repositories': df['repository'].nunique(),
            'date_range': f"{df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}",
            'avg_traditional_quality': df['quality_score'].mean(),
            'avg_llm_quality': df.get('llm_quality_score', pd.Series([0])).mean(),
            'avg_business_impact': df.get('business_impact_score', pd.Series([0])).mean(),
            'total_lines_added': df.get('additions', pd.Series([0])).sum(),
            'total_lines_deleted': df.get('deletions', pd.Series([0])).sum(),
            'high_impact_commits': len(df[df.get('business_impact_score', 0) > 7]) if 'business_impact_score' in df.columns else 0
        }
    
    def _calculate_comparative_metrics(self, df: pd.DataFrame) -> Dict:
        """Calculate comparative developer metrics"""
        dev_metrics = df.groupby('author').agg({
            'sha': 'count',
            'quality_score': 'mean',
            'additions': 'sum',
            'deletions': 'sum',
            'total_changes': 'sum'
        }).rename(columns={'sha': 'commit_count'})
        
        if 'llm_quality_score' in df.columns:
            dev_metrics['llm_quality'] = df.groupby('author')['llm_quality_score'].mean()
            dev_metrics['business_impact'] = df.groupby('author')['business_impact_score'].mean()
        
        # Calculate percentiles and rankings
        metrics = {}
        for dev in dev_metrics.index:
            dev_data = dev_metrics.loc[dev]
            metrics[dev] = {
                'commits': int(dev_data['commit_count']),
                'quality_percentile': self._calculate_percentile(dev_data['quality_score'], dev_metrics['quality_score']),
                'productivity_percentile': self._calculate_percentile(dev_data['total_changes'], dev_metrics['total_changes']),
                'lines_added': int(dev_data['additions']),
                'lines_deleted': int(dev_data['deletions']),
                'avg_quality': round(dev_data['quality_score'], 2)
            }
            
            if 'llm_quality' in dev_metrics.columns:
                metrics[dev]['llm_quality'] = round(dev_data['llm_quality'], 2)
                metrics[dev]['business_impact'] = round(dev_data['business_impact'], 2)
        
        return metrics
    
    def _calculate_percentile(self, value: float, series: pd.Series) -> int:
        """Calculate percentile rank"""
        return int((series < value).mean() * 100)
    
    def _calculate_developer_rankings(self, df: pd.DataFrame) -> Dict:
        """Calculate developer rankings across different metrics"""
        dev_stats = df.groupby('author').agg({
            'sha': 'count',
            'quality_score': 'mean',
            'total_changes': 'sum',
        }).rename(columns={'sha': 'commits'})
        
        if 'business_impact_score' in df.columns:
            dev_stats['business_impact'] = df.groupby('author')['business_impact_score'].mean()
        
        rankings = {}
        metrics = ['commits', 'quality_score', 'total_changes']
        if 'business_impact' in dev_stats.columns:
            metrics.append('business_impact')
        
        for metric in metrics:
            rankings[f'top_{metric}'] = dev_stats.nlargest(5, metric).reset_index()
        
        return rankings
    
    def _create_time_series_data(self, df: pd.DataFrame) -> Dict:
        """Create time series data for various metrics"""
        df_copy = df.copy()
        df_copy['date'] = pd.to_datetime(df_copy['date'])
        df_copy['week'] = df_copy['date'].dt.to_period('W').dt.start_time
        df_copy['month'] = df_copy['date'].dt.to_period('M').dt.start_time
        
        # Weekly aggregations
        weekly_data = df_copy.groupby(['author', 'week']).agg({
            'sha': 'count',
            'quality_score': 'mean',
            'total_changes': 'sum'
        }).reset_index()
        weekly_data.columns = ['developer', 'week', 'commits', 'avg_quality', 'lines_changed']
        
        if 'business_impact_score' in df_copy.columns:
            weekly_impact = df_copy.groupby(['author', 'week'])['business_impact_score'].mean().reset_index()
            weekly_data = weekly_data.merge(weekly_impact, left_on=['developer', 'week'], right_on=['author', 'week'], how='left')
        
        # Monthly aggregations
        monthly_data = df_copy.groupby(['author', 'month']).agg({
            'sha': 'count',
            'quality_score': 'mean',
            'total_changes': 'sum'
        }).reset_index()
        monthly_data.columns = ['developer', 'month', 'commits', 'avg_quality', 'lines_changed']
        
        return {
            'weekly': weekly_data,
            'monthly': monthly_data
        }
    
    def _create_enhanced_charts(self, df: pd.DataFrame, summaries: List[DeveloperPeriodSummary]) -> Dict:
        """Create enhanced visualization charts"""
        charts = {}
        
        # 1. Developer Performance Radar Chart
        charts['performance_radar'] = self._create_performance_radar_chart(df)
        
        # 2. Business Impact vs Technical Quality Scatter
        if 'business_impact_score' in df.columns:
            charts['impact_vs_quality'] = self._create_impact_quality_scatter(df)
        
        # 3. Feature Type Distribution by Developer
        if 'feature_type' in df.columns:
            charts['feature_distribution'] = self._create_feature_type_distribution(df)
        
        # 4. Complexity Trend Over Time
        if 'complexity_level' in df.columns:
            charts['complexity_trends'] = self._create_complexity_trends(df)
        
        # 5. Developer Changelog Timeline
        charts['changelog_timeline'] = self._create_changelog_timeline(summaries)
        
        # 6. Comparative Performance Matrix
        charts['performance_matrix'] = self._create_performance_matrix(df)
        
        # 7. Risk Level Distribution
        if 'risk_level' in df.columns:
            charts['risk_distribution'] = self._create_risk_distribution(df)
        
        return charts
    
    def _create_performance_radar_chart(self, df: pd.DataFrame) -> go.Figure:
        """Create radar chart for developer performance comparison"""
        # Calculate metrics per developer
        dev_metrics = df.groupby('author').agg({
            'quality_score': 'mean',
            'total_changes': lambda x: np.log1p(x.sum()),  # Log scale for large numbers
            'sha': 'count'
        }).round(2)
        
        if 'business_impact_score' in df.columns:
            dev_metrics['business_impact'] = df.groupby('author')['business_impact_score'].mean()
        
        # Normalize to 0-10 scale
        for col in dev_metrics.columns:
            dev_metrics[col] = (dev_metrics[col] - dev_metrics[col].min()) / (dev_metrics[col].max() - dev_metrics[col].min()) * 10
        
        fig = go.Figure()
        
        metrics = list(dev_metrics.columns)
        for developer in dev_metrics.index:
            values = dev_metrics.loc[developer].tolist()
            values.append(values[0])  # Close the radar chart
            
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=metrics + [metrics[0]],
                fill='toself',
                name=developer,
                opacity=0.7
            ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 10])
            ),
            showlegend=True,
            title="Developer Performance Radar Chart"
        )
        
        return fig
    
    def _create_impact_quality_scatter(self, df: pd.DataFrame) -> go.Figure:
        """Create scatter plot of business impact vs technical quality"""
        dev_data = df.groupby('author').agg({
            'business_impact_score': 'mean',
            'quality_score': 'mean',
            'sha': 'count',
            'total_changes': 'sum'
        }).reset_index()
        
        fig = px.scatter(
            dev_data,
            x='quality_score',
            y='business_impact_score',
            size='total_changes',
            hover_name='author',
            hover_data=['sha'],
            title='Developer Performance: Business Impact vs Technical Quality',
            labels={
                'quality_score': 'Technical Quality Score',
                'business_impact_score': 'Business Impact Score',
                'sha': 'Total Commits'
            }
        )
        
        # Add quadrant lines
        fig.add_hline(y=5, line_dash="dash", line_color="gray")
        fig.add_vline(x=5, line_dash="dash", line_color="gray")
        
        return fig
    
    def _create_feature_type_distribution(self, df: pd.DataFrame) -> go.Figure:
        """Create stacked bar chart of feature types by developer"""
        feature_counts = pd.crosstab(df['author'], df['feature_type'])
        
        fig = go.Figure()
        
        colors = px.colors.qualitative.Set3
        for i, feature_type in enumerate(feature_counts.columns):
            fig.add_trace(go.Bar(
                name=feature_type,
                x=feature_counts.index,
                y=feature_counts[feature_type],
                marker_color=colors[i % len(colors)]
            ))
        
        fig.update_layout(
            barmode='stack',
            title='Feature Type Distribution by Developer',
            xaxis_title='Developer',
            yaxis_title='Number of Commits'
        )
        
        return fig
    
    def _create_complexity_trends(self, df: pd.DataFrame) -> go.Figure:
        """Create complexity trends over time"""
        df_copy = df.copy()
        df_copy['week'] = pd.to_datetime(df_copy['date']).dt.to_period('W').dt.start_time
        
        # Map complexity to numeric values
        complexity_map = {'low': 1, 'medium': 2, 'high': 3, 'very_high': 4}
        df_copy['complexity_numeric'] = df_copy['complexity_level'].map(complexity_map)
        
        weekly_complexity = df_copy.groupby(['author', 'week'])['complexity_numeric'].mean().reset_index()
        
        fig = px.line(
            weekly_complexity,
            x='week',
            y='complexity_numeric',
            color='author',
            title='Complexity Trends Over Time',
            labels={
                'complexity_numeric': 'Average Complexity Level',
                'week': 'Week'
            }
        )
        
        return fig
    
    def _create_changelog_timeline(self, summaries: List[DeveloperPeriodSummary]) -> go.Figure:
        """Create timeline view of developer achievements"""
        fig = go.Figure()
        
        y_positions = {}
        y_counter = 0
        
        for summary in summaries:
            if summary.developer not in y_positions:
                y_positions[summary.developer] = y_counter
                y_counter += 1
            
            # Create timeline entries for achievements
            for i, achievement in enumerate(summary.key_achievements):
                fig.add_trace(go.Scatter(
                    x=[summary.period_start],
                    y=[y_positions[summary.developer]],
                    mode='markers+text',
                    marker=dict(size=15, color='blue'),
                    text=achievement[:30] + '...' if len(achievement) > 30 else achievement,
                    textposition='middle right',
                    name=f"{summary.developer}",
                    showlegend=False if i > 0 else True
                ))
        
        fig.update_layout(
            title='Developer Achievement Timeline',
            xaxis_title='Time Period',
            yaxis=dict(
                tickmode='array',
                tickvals=list(y_positions.values()),
                ticktext=list(y_positions.keys())
            )
        )
        
        return fig
    
    def _create_performance_matrix(self, df: pd.DataFrame) -> go.Figure:
        """Create performance comparison matrix"""
        metrics = ['quality_score', 'total_changes', 'sha']
        if 'business_impact_score' in df.columns:
            metrics.append('business_impact_score')
        
        dev_metrics = df.groupby('author').agg({
            'quality_score': 'mean',
            'total_changes': 'sum',
            'sha': 'count',
            'business_impact_score': 'mean' if 'business_impact_score' in df.columns else lambda x: 0
        })
        
        # Normalize for comparison
        normalized_metrics = dev_metrics.copy()
        for col in normalized_metrics.columns:
            normalized_metrics[col] = (normalized_metrics[col] - normalized_metrics[col].min()) / (normalized_metrics[col].max() - normalized_metrics[col].min())
        
        fig = go.Figure(data=go.Heatmap(
            z=normalized_metrics.values,
            x=normalized_metrics.columns,
            y=normalized_metrics.index,
            colorscale='RdYlBu_r',
            text=dev_metrics.round(2).values,
            texttemplate="%{text}",
            textfont={"size": 10}
        ))
        
        fig.update_layout(
            title='Developer Performance Matrix (Normalized)',
            xaxis_title='Metrics',
            yaxis_title='Developers'
        )
        
        return fig
    
    def _create_risk_distribution(self, df: pd.DataFrame) -> go.Figure:
        """Create risk level distribution chart"""
        risk_counts = df.groupby(['author', 'risk_level']).size().reset_index(name='count')
        
        fig = px.bar(
            risk_counts,
            x='author',
            y='count',
            color='risk_level',
            title='Risk Level Distribution by Developer',
            color_discrete_map={
                'low': 'green',
                'medium': 'yellow',
                'high': 'red'
            }
        )
        
        return fig
    
    def _create_enhanced_html(self, dashboard_data: Dict) -> str:
        """Create enhanced HTML dashboard with all visualizations"""
        
        html_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>Enhanced Developer Analytics Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        
        .dashboard-container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 20px 60px rgba(0,0,0,0.1);
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        
        .header .subtitle {{
            margin-top: 10px;
            opacity: 0.9;
            font-size: 1.1em;
        }}
        
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}
        
        .summary-card {{
            background: white;
            padding: 25px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 4px 20px rgba(0,0,0,0.05);
            border-left: 4px solid #667eea;
        }}
        
        .summary-card .value {{
            font-size: 2.2em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 8px;
        }}
        
        .summary-card .label {{
            color: #6c757d;
            font-size: 0.95em;
        }}
        
        .tabs {{
            display: flex;
            background: #f8f9fa;
            padding: 0 30px;
            flex-wrap: wrap;
        }}
        
        .tab-button {{
            padding: 15px 25px;
            border: none;
            background: transparent;
            cursor: pointer;
            font-weight: 500;
            color: #6c757d;
            border-bottom: 3px solid transparent;
            transition: all 0.3s ease;
        }}
        
        .tab-button.active {{
            color: #667eea;
            border-bottom-color: #667eea;
        }}
        
        .tab-content {{
            display: none;
            padding: 30px;
        }}
        
        .tab-content.active {{
            display: block;
        }}
        
        .chart-grid {{
            display: grid;
            gap: 30px;
            margin-top: 20px;
        }}
        
        .chart-container {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.05);
        }}
        
        .two-column {{
            grid-template-columns: 1fr 1fr;
        }}
        
        .three-column {{
            grid-template-columns: repeat(3, 1fr);
        }}
        
        @media (max-width: 1024px) {{
            .two-column, .three-column {{
                grid-template-columns: 1fr;
            }}
        }}
        
        .developer-summary {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            margin: 20px 0;
            box-shadow: 0 4px 20px rgba(0,0,0,0.05);
        }}
        
        .developer-name {{
            font-size: 1.4em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 15px;
        }}
        
        .achievement-list {{
            list-style: none;
            padding: 0;
        }}
        
        .achievement-list li {{
            padding: 8px 0;
            border-bottom: 1px solid #e9ecef;
        }}
        
        .achievement-list li:before {{
            content: "✓";
            color: #28a745;
            font-weight: bold;
            margin-right: 10px;
        }}
    </style>
</head>
<body>
    <div class="dashboard-container">
        <div class="header">
            <h1>🚀 Enhanced Developer Analytics</h1>
            <div class="subtitle">LLM-Powered Insights & Comparative Performance Analysis</div>
            <div style="margin-top: 20px; font-size: 0.9em; opacity: 0.8;">
                Generated: {generation_time} | Period: {date_range}
            </div>
        </div>
        
        <div class="summary-grid">
            <div class="summary-card">
                <div class="value">{total_commits:,}</div>
                <div class="label">Total Commits</div>
            </div>
            <div class="summary-card">
                <div class="value">{total_developers}</div>
                <div class="label">Active Developers</div>
            </div>
            <div class="summary-card">
                <div class="value">{total_repositories}</div>
                <div class="label">Repositories</div>
            </div>
            <div class="summary-card">
                <div class="value">{avg_traditional_quality:.1f}</div>
                <div class="label">Avg Quality Score</div>
            </div>
            <div class="summary-card">
                <div class="value">{avg_llm_quality:.1f}</div>
                <div class="label">Avg LLM Quality</div>
            </div>
            <div class="summary-card">
                <div class="value">{high_impact_commits}</div>
                <div class="label">High Impact Commits</div>
            </div>
        </div>
        
        <div class="tabs">
            <button class="tab-button active" onclick="openTab(event, 'overview')">Overview</button>
            <button class="tab-button" onclick="openTab(event, 'comparative')">Comparative Analysis</button>
            <button class="tab-button" onclick="openTab(event, 'timeseries')">Time Series</button>
            <button class="tab-button" onclick="openTab(event, 'summaries')">Developer Summaries</button>
        </div>
        
        <div id="overview" class="tab-content active">
            <div class="chart-grid two-column">
                <div class="chart-container">
                    {performance_radar}
                </div>
                <div class="chart-container">
                    {impact_vs_quality}
                </div>
            </div>
            
            <div class="chart-grid">
                <div class="chart-container">
                    {performance_matrix}
                </div>
            </div>
        </div>
        
        <div id="comparative" class="tab-content">
            <div class="chart-grid two-column">
                <div class="chart-container">
                    {feature_distribution}
                </div>
                <div class="chart-container">
                    {risk_distribution}
                </div>
            </div>
        </div>
        
        <div id="timeseries" class="tab-content">
            <div class="chart-grid">
                <div class="chart-container">
                    {complexity_trends}
                </div>
            </div>
            <div class="chart-grid">
                <div class="chart-container">
                    {changelog_timeline}
                </div>
            </div>
        </div>
        
        <div id="summaries" class="tab-content">
            {developer_summaries_html}
        </div>
    </div>
    
    <script>
        function openTab(evt, tabName) {{
            var i, tabcontent, tablinks;
            tabcontent = document.getElementsByClassName("tab-content");
            for (i = 0; i < tabcontent.length; i++) {{
                tabcontent[i].classList.remove("active");
            }}
            tablinks = document.getElementsByClassName("tab-button");
            for (i = 0; i < tablinks.length; i++) {{
                tablinks[i].classList.remove("active");
            }}
            document.getElementById(tabName).classList.add("active");
            evt.currentTarget.classList.add("active");
            
            // Trigger Plotly relayout for responsive charts
            setTimeout(function() {{
                window.dispatchEvent(new Event('resize'));
            }}, 100);
        }}
        
        // Make charts responsive
        window.addEventListener('resize', function() {{
            var plotElements = document.querySelectorAll('.plotly-graph-div');
            plotElements.forEach(function(element) {{
                if (element.style.display !== 'none') {{
                    Plotly.Plots.resize(element);
                }}
            }});
        }});
    </script>
</body>
</html>
        '''
        
        # Generate developer summaries HTML
        summaries_html = ""
        for summary in dashboard_data['summaries']:
            achievements_html = ""
            for achievement in summary.key_achievements:
                achievements_html += f"<li>{achievement}</li>"
            
            features_html = ", ".join(summary.features_completed[:3]) if summary.features_completed else "No major features"
            
            summaries_html += f'''
            <div class="developer-summary">
                <div class="developer-name">{summary.developer}</div>
                <div><strong>Period:</strong> {summary.period_start[:10]} to {summary.period_end[:10]}</div>
                <div><strong>Key Features:</strong> {features_html}</div>
                <div><strong>Quality Trend:</strong> {summary.overall_quality_trend}</div>
                <div><strong>Technical Depth:</strong> {summary.technical_depth}</div>
                <div><strong>Key Achievements:</strong></div>
                <ul class="achievement-list">
                    {achievements_html}
                </ul>
            </div>
            '''
        
        # Format the template with data
        stats = dashboard_data['summary_stats']
        charts = dashboard_data['charts']
        
        return html_template.format(
            generation_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            date_range=stats['date_range'],
            total_commits=stats['total_commits'],
            total_developers=stats['total_developers'],
            total_repositories=stats['total_repositories'],
            avg_traditional_quality=stats['avg_traditional_quality'],
            avg_llm_quality=stats.get('avg_llm_quality', 0),
            high_impact_commits=stats.get('high_impact_commits', 0),
            performance_radar=charts.get('performance_radar', go.Figure()).to_html(include_plotlyjs=False, full_html=False),
            impact_vs_quality=charts.get('impact_vs_quality', go.Figure()).to_html(include_plotlyjs=False, full_html=False),
            performance_matrix=charts.get('performance_matrix', go.Figure()).to_html(include_plotlyjs=False, full_html=False),
            feature_distribution=charts.get('feature_distribution', go.Figure()).to_html(include_plotlyjs=False, full_html=False),
            risk_distribution=charts.get('risk_distribution', go.Figure()).to_html(include_plotlyjs=False, full_html=False),
            complexity_trends=charts.get('complexity_trends', go.Figure()).to_html(include_plotlyjs=False, full_html=False),
            changelog_timeline=charts.get('changelog_timeline', go.Figure()).to_html(include_plotlyjs=False, full_html=False),
            developer_summaries_html=summaries_html
        )

async def main():
    """Main function to generate enhanced dashboard"""
    generator = EnhancedDashboardGenerator()
    await generator.create_enhanced_dashboard()

if __name__ == '__main__':
    asyncio.run(main())