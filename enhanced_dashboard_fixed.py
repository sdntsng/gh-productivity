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
import json

class FixedEnhancedDashboardGenerator:
    """Generate enhanced dashboard with proper fallbacks for missing LLM data"""
    
    def __init__(self):
        pass
        
    async def create_enhanced_dashboard(self, commits_csv: str = None, out_html: str = None):
        """Create enhanced dashboard with better data handling"""
        
        # Load data
        commits_csv = commits_csv or config.COMMIT_ANALYSIS_FILE
        out_html = out_html or "enhanced_dashboard.html"
        
        print("Loading commit data...")
        commits_df = self._load_and_prepare_data(commits_csv)
        
        # Generate enhanced insights from existing data
        print("Generating enhanced insights...")
        enhanced_data = self._generate_enhanced_insights(commits_df)
        
        # Create comprehensive dashboard data
        print("Creating comprehensive visualizations...")
        dashboard_data = self._create_comprehensive_dashboard_data(commits_df, enhanced_data)
        
        # Generate HTML dashboard
        print("Generating HTML dashboard...")
        html_content = self._create_comprehensive_html(dashboard_data)
        
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
    
    def _generate_enhanced_insights(self, commits_df: pd.DataFrame) -> Dict:
        """Generate insights from traditional metrics with intelligent classification"""
        
        # Classify commits based on message content
        commits_df = self._classify_commits(commits_df)
        
        # Generate developer summaries
        developer_summaries = self._create_intelligent_summaries(commits_df)
        
        return {
            'classified_commits': commits_df,
            'developer_summaries': developer_summaries,
            'time_series_insights': self._create_time_series_insights(commits_df)
        }
    
    def _classify_commits(self, df: pd.DataFrame) -> pd.DataFrame:
        """Intelligently classify commits based on message patterns"""
        df = df.copy()
        
        # Feature type classification based on commit messages
        def classify_feature_type(message):
            message_lower = message.lower()
            if any(word in message_lower for word in ['feat', 'feature', 'add', 'implement', 'create']):
                return 'feature'
            elif any(word in message_lower for word in ['fix', 'bug', 'issue', 'error', 'resolve']):
                return 'bugfix'  
            elif any(word in message_lower for word in ['refactor', 'cleanup', 'reorganize', 'restructure']):
                return 'refactoring'
            elif any(word in message_lower for word in ['test', 'spec', 'tests']):
                return 'testing'
            elif any(word in message_lower for word in ['doc', 'readme', 'comment', 'documentation']):
                return 'documentation'
            else:
                return 'maintenance'
        
        # Complexity classification based on lines changed and files
        def classify_complexity(total_changes, message):
            message_lower = message.lower()
            if total_changes > 1000 or any(word in message_lower for word in ['major', 'significant', 'overhaul', 'rewrite']):
                return 'very_high'
            elif total_changes > 500 or any(word in message_lower for word in ['complex', 'extensive', 'comprehensive']):
                return 'high'
            elif total_changes > 100 or any(word in message_lower for word in ['enhance', 'improve', 'extend']):
                return 'medium'
            else:
                return 'low'
        
        # Risk classification based on patterns
        def classify_risk(is_hotfix, message, total_changes):
            message_lower = message.lower()
            if is_hotfix or any(word in message_lower for word in ['critical', 'urgent', 'emergency']):
                return 'high'
            elif total_changes > 500 or any(word in message_lower for word in ['breaking', 'migration', 'major']):
                return 'medium'
            else:
                return 'low'
        
        # Apply classifications
        df['feature_type'] = df['message'].apply(classify_feature_type)
        df['complexity_level'] = df.apply(lambda row: classify_complexity(row['total_changes'], row['message']), axis=1)
        df['risk_level'] = df.apply(lambda row: classify_risk(row['is_hotfix'], row['message'], row['total_changes']), axis=1)
        
        # Business impact scoring (0-10) based on multiple factors
        def calculate_business_impact(row):
            score = 5.0  # Base score
            
            # Feature type impact
            if row['feature_type'] == 'feature':
                score += 2.0
            elif row['feature_type'] == 'bugfix':
                score += 1.5
            elif row['feature_type'] == 'refactoring':
                score += 1.0
            
            # Size impact
            if row['total_changes'] > 1000:
                score += 1.5
            elif row['total_changes'] > 500:
                score += 1.0
            elif row['total_changes'] > 100:
                score += 0.5
            
            # Quality factors
            if row['has_issue_ref']:
                score += 0.5
            if row['follows_convention']:
                score += 0.5
                
            # Negative factors
            if row['is_hotfix']:
                score -= 1.0
            if row['is_revert']:
                score -= 2.0
                
            return min(10.0, max(0.0, score))
        
        df['business_impact_score'] = df.apply(calculate_business_impact, axis=1)
        
        return df
    
    def _create_intelligent_summaries(self, df: pd.DataFrame) -> List[Dict]:
        """Create intelligent developer summaries from commit patterns"""
        summaries = []
        
        # Group by developer and create weekly summaries
        for developer in df['author'].unique():
            dev_commits = df[df['author'] == developer].copy()
            
            # Get recent work (last 4 weeks)
            recent_date = dev_commits['date'].max()
            four_weeks_ago = recent_date - timedelta(weeks=4)
            recent_commits = dev_commits[dev_commits['date'] >= four_weeks_ago]
            
            if recent_commits.empty:
                continue
                
            # Analyze work patterns
            features = recent_commits[recent_commits['feature_type'] == 'feature']
            bugs = recent_commits[recent_commits['feature_type'] == 'bugfix']
            refactoring = recent_commits[recent_commits['feature_type'] == 'refactoring']
            
            # Extract key accomplishments from commit messages
            key_features = self._extract_key_work(features['message'].tolist(), 'features')
            key_bugs = self._extract_key_work(bugs['message'].tolist(), 'fixes')
            key_refactoring = self._extract_key_work(refactoring['message'].tolist(), 'improvements')
            
            # Calculate quality trend
            quality_scores = recent_commits['quality_score'].tolist()
            if len(quality_scores) > 1:
                first_half_avg = np.mean(quality_scores[:len(quality_scores)//2])
                second_half_avg = np.mean(quality_scores[len(quality_scores)//2:])
                trend = "improving" if second_half_avg > first_half_avg + 0.5 else \
                       "declining" if second_half_avg < first_half_avg - 0.5 else "stable"
            else:
                trend = "stable"
            
            # Assess technical depth
            complex_work = recent_commits[recent_commits['complexity_level'].isin(['high', 'very_high'])]
            depth = "deep" if len(complex_work) / len(recent_commits) > 0.3 else \
                   "moderate" if len(complex_work) / len(recent_commits) > 0.1 else "surface"
            
            # Generate achievements based on metrics
            achievements = []
            if len(features) > 0:
                achievements.append(f"Delivered {len(features)} new features")
            if len(bugs) > 0:
                achievements.append(f"Fixed {len(bugs)} issues")
            if recent_commits['quality_score'].mean() > 6.5:
                achievements.append("Maintained high code quality")
            if recent_commits['total_changes'].sum() > 10000:
                achievements.append("Contributed significant code volume")
            if recent_commits['business_impact_score'].mean() > 7.0:
                achievements.append("Delivered high business impact")
            
            summary = {
                'developer': developer,
                'period_start': four_weeks_ago.strftime('%Y-%m-%d'),
                'period_end': recent_date.strftime('%Y-%m-%d'),
                'key_features': key_features,
                'key_bugs': key_bugs,
                'key_refactoring': key_refactoring,
                'quality_trend': trend,
                'technical_depth': depth,
                'achievements': achievements,
                'stats': {
                    'total_commits': len(recent_commits),
                    'avg_quality': round(recent_commits['quality_score'].mean(), 1),
                    'avg_business_impact': round(recent_commits['business_impact_score'].mean(), 1),
                    'lines_changed': recent_commits['total_changes'].sum()
                }
            }
            summaries.append(summary)
        
        return summaries
    
    def _extract_key_work(self, messages: List[str], work_type: str) -> List[str]:
        """Extract key work items from commit messages"""
        if not messages:
            return []
        
        # Clean and deduplicate messages
        cleaned_messages = []
        seen = set()
        
        for msg in messages:
            # Clean up the message
            clean_msg = msg.split('\n')[0].strip()  # First line only
            clean_msg = clean_msg.replace('feat:', '').replace('fix:', '').replace('refactor:', '').strip()
            
            # Remove common prefixes
            for prefix in ['add ', 'fix ', 'update ', 'improve ', 'implement ', 'create ']:
                if clean_msg.lower().startswith(prefix):
                    clean_msg = clean_msg[len(prefix):].strip()
            
            # Avoid duplicates and very short messages
            if len(clean_msg) > 10 and clean_msg.lower() not in seen:
                cleaned_messages.append(clean_msg[:60])  # Limit length
                seen.add(clean_msg.lower())
        
        return cleaned_messages[:5]  # Top 5 items
    
    def _create_time_series_insights(self, df: pd.DataFrame) -> Dict:
        """Create time series insights for trend analysis"""
        df_copy = df.copy()
        df_copy['week'] = df_copy['date'].dt.to_period('W').dt.start_time
        df_copy['month'] = df_copy['date'].dt.to_period('M').dt.start_time
        
        # Weekly aggregations
        weekly_data = df_copy.groupby(['author', 'week']).agg({
            'sha': 'count',
            'quality_score': 'mean',
            'business_impact_score': 'mean',
            'total_changes': 'sum'
        }).reset_index()
        weekly_data.columns = ['developer', 'week', 'commits', 'avg_quality', 'avg_business_impact', 'lines_changed']
        
        return {'weekly': weekly_data}
    
    def _create_comprehensive_dashboard_data(self, commits_df: pd.DataFrame, enhanced_data: Dict) -> Dict:
        """Create comprehensive dashboard data"""
        
        classified_df = enhanced_data['classified_commits']
        
        dashboard_data = {
            'commits_df': classified_df,
            'developer_summaries': enhanced_data['developer_summaries'],
            'time_series_data': enhanced_data['time_series_insights'],
            'summary_stats': self._calculate_enhanced_summary_stats(classified_df),
            'charts': {}
        }
        
        # Create enhanced charts
        dashboard_data['charts'] = self._create_enhanced_charts(classified_df, enhanced_data['developer_summaries'])
        
        return dashboard_data
    
    def _calculate_enhanced_summary_stats(self, df: pd.DataFrame) -> Dict:
        """Calculate comprehensive summary statistics"""
        return {
            'total_commits': len(df),
            'total_developers': df['author'].nunique(),
            'total_repositories': df['repository'].nunique(),
            'date_range': f"{df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}",
            'avg_traditional_quality': df['quality_score'].mean(),
            'avg_business_impact': df['business_impact_score'].mean(),
            'total_lines_added': df['additions'].sum(),
            'total_lines_deleted': df['deletions'].sum(),
            'high_impact_commits': len(df[df['business_impact_score'] > 7]),
            'feature_commits': len(df[df['feature_type'] == 'feature']),
            'bug_fix_commits': len(df[df['feature_type'] == 'bugfix'])
        }
    
    def _create_enhanced_charts(self, df: pd.DataFrame, summaries: List[Dict]) -> Dict:
        """Create enhanced visualization charts with proper data"""
        charts = {}
        
        # 1. Developer Performance Radar Chart
        charts['performance_radar'] = self._create_performance_radar_chart(df)
        
        # 2. Business Impact vs Technical Quality Scatter
        charts['impact_vs_quality'] = self._create_impact_quality_scatter(df)
        
        # 3. Feature Type Distribution by Developer
        charts['feature_distribution'] = self._create_feature_type_distribution(df)
        
        # 4. Complexity Trends Over Time
        charts['complexity_trends'] = self._create_complexity_trends(df)
        
        # 5. Developer Achievement Timeline
        charts['achievement_timeline'] = self._create_achievement_timeline(summaries)
        
        # 6. Comparative Performance Matrix
        charts['performance_matrix'] = self._create_performance_matrix(df)
        
        # 7. Risk Level Distribution
        charts['risk_distribution'] = self._create_risk_distribution(df)
        
        # 8. Weekly Productivity Trends
        charts['weekly_trends'] = self._create_weekly_trends(df)
        
        return charts
    
    def _create_performance_radar_chart(self, df: pd.DataFrame) -> go.Figure:
        """Create radar chart for developer performance comparison"""
        dev_metrics = df.groupby('author').agg({
            'quality_score': 'mean',
            'business_impact_score': 'mean',
            'total_changes': lambda x: np.log1p(x.sum()),
            'sha': 'count'
        }).round(2)
        
        # Normalize to 0-10 scale
        for col in dev_metrics.columns:
            col_min = dev_metrics[col].min()
            col_max = dev_metrics[col].max()
            if col_max > col_min:
                dev_metrics[col] = (dev_metrics[col] - col_min) / (col_max - col_min) * 10
            else:
                dev_metrics[col] = 5  # Default middle value if all same
        
        fig = go.Figure()
        
        metrics = ['Quality', 'Business Impact', 'Code Volume', 'Commit Count']
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
            polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
            showlegend=True,
            title="Developer Performance Radar Chart",
            height=500
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
        fig.add_hline(y=5, line_dash="dash", line_color="gray", annotation_text="Average Impact")
        fig.add_vline(x=5, line_dash="dash", line_color="gray", annotation_text="Average Quality")
        
        fig.update_layout(height=500)
        return fig
    
    def _create_feature_type_distribution(self, df: pd.DataFrame) -> go.Figure:
        """Create stacked bar chart of feature types by developer"""
        feature_counts = pd.crosstab(df['author'], df['feature_type'])
        
        fig = go.Figure()
        
        colors = px.colors.qualitative.Set3
        for i, feature_type in enumerate(feature_counts.columns):
            fig.add_trace(go.Bar(
                name=feature_type.title(),
                x=feature_counts.index,
                y=feature_counts[feature_type],
                marker_color=colors[i % len(colors)]
            ))
        
        fig.update_layout(
            barmode='stack',
            title='Work Type Distribution by Developer',
            xaxis_title='Developer',
            yaxis_title='Number of Commits',
            height=500
        )
        
        return fig
    
    def _create_complexity_trends(self, df: pd.DataFrame) -> go.Figure:
        """Create complexity trends over time"""
        df_copy = df.copy()
        df_copy['week'] = df_copy['date'].dt.to_period('W').dt.start_time
        
        # Map complexity to numeric values
        complexity_map = {'low': 1, 'medium': 2, 'high': 3, 'very_high': 4}
        df_copy['complexity_numeric'] = df_copy['complexity_level'].map(complexity_map)
        
        weekly_complexity = df_copy.groupby(['author', 'week'])['complexity_numeric'].mean().reset_index()
        
        if not weekly_complexity.empty:
            fig = px.line(
                weekly_complexity,
                x='week',
                y='complexity_numeric',
                color='author',
                title='Technical Complexity Trends Over Time',
                labels={'complexity_numeric': 'Average Complexity Level', 'week': 'Week'}
            )
            fig.update_layout(height=500)
        else:
            fig = go.Figure()
            fig.update_layout(title='Technical Complexity Trends - No Data Available', height=500)
        
        return fig
    
    def _create_achievement_timeline(self, summaries: List[Dict]) -> go.Figure:
        """Create timeline view of developer achievements"""
        fig = go.Figure()
        
        if not summaries:
            fig.update_layout(title='Developer Achievement Timeline - No Data Available', height=500)
            return fig
        
        y_positions = {}
        y_counter = 0
        
        for summary in summaries:
            if summary['developer'] not in y_positions:
                y_positions[summary['developer']] = y_counter
                y_counter += 1
            
            # Create timeline entries for achievements
            achievements_text = '; '.join(summary['achievements'][:2]) if summary['achievements'] else 'Recent contributions'
            period_text = f"{summary['period_start']} - {summary['period_end']}"
            
            fig.add_trace(go.Scatter(
                x=[summary['period_end']],
                y=[y_positions[summary['developer']]],
                mode='markers+text',
                marker=dict(size=20, color=px.colors.qualitative.Set1[y_positions[summary['developer']] % len(px.colors.qualitative.Set1)]),
                text=achievements_text[:50] + '...' if len(achievements_text) > 50 else achievements_text,
                textposition='middle right',
                name=summary['developer'],
                showlegend=True,
                hovertemplate=f"<b>{summary['developer']}</b><br>{period_text}<br>{achievements_text}<extra></extra>"
            ))
        
        fig.update_layout(
            title='Developer Achievement Timeline',
            xaxis_title='Time Period',
            yaxis=dict(
                tickmode='array',
                tickvals=list(y_positions.values()),
                ticktext=list(y_positions.keys())
            ),
            height=500
        )
        
        return fig
    
    def _create_performance_matrix(self, df: pd.DataFrame) -> go.Figure:
        """Create performance comparison matrix"""
        metrics = ['quality_score', 'business_impact_score', 'total_changes', 'sha']
        
        dev_metrics = df.groupby('author').agg({
            'quality_score': 'mean',
            'business_impact_score': 'mean', 
            'total_changes': 'sum',
            'sha': 'count'
        }).round(2)
        
        # Normalize for comparison (0-1 scale)
        normalized_metrics = dev_metrics.copy()
        for col in normalized_metrics.columns:
            col_min = normalized_metrics[col].min()
            col_max = normalized_metrics[col].max()
            if col_max > col_min:
                normalized_metrics[col] = (normalized_metrics[col] - col_min) / (col_max - col_min)
            else:
                normalized_metrics[col] = 0.5
        
        fig = go.Figure(data=go.Heatmap(
            z=normalized_metrics.values,
            x=['Quality Score', 'Business Impact', 'Lines Changed', 'Commit Count'],
            y=normalized_metrics.index,
            colorscale='RdYlBu_r',
            text=dev_metrics.values,
            texttemplate="%{text}",
            textfont={"size": 12},
            hovertemplate="Developer: %{y}<br>Metric: %{x}<br>Value: %{text}<br>Normalized: %{z:.2f}<extra></extra>"
        ))
        
        fig.update_layout(
            title='Developer Performance Matrix',
            xaxis_title='Metrics',
            yaxis_title='Developers',
            height=400
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
                'low': '#2E8B57',      # Sea Green
                'medium': '#FFD700',   # Gold  
                'high': '#DC143C'      # Crimson
            }
        )
        
        fig.update_layout(height=400)
        return fig
    
    def _create_weekly_trends(self, df: pd.DataFrame) -> go.Figure:
        """Create weekly productivity trends"""
        df_copy = df.copy()
        df_copy['week'] = df_copy['date'].dt.to_period('W').dt.start_time
        
        weekly_stats = df_copy.groupby(['author', 'week']).agg({
            'sha': 'count',
            'business_impact_score': 'mean'
        }).reset_index()
        
        fig = px.line(
            weekly_stats,
            x='week', 
            y='business_impact_score',
            color='author',
            title='Weekly Business Impact Trends',
            labels={'business_impact_score': 'Average Business Impact', 'week': 'Week'}
        )
        
        fig.update_layout(height=500)
        return fig
    
    def _create_comprehensive_html(self, dashboard_data: Dict) -> str:
        """Create comprehensive HTML dashboard"""
        
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
            border-left: 5px solid #667eea;
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
            margin: 10px 0;
        }}
        
        .achievement-list li {{
            padding: 8px 0;
            border-bottom: 1px solid #e9ecef;
            color: #495057;
        }}
        
        .achievement-list li:before {{
            content: "✓";
            color: #28a745;
            font-weight: bold;
            margin-right: 10px;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 15px;
            margin-top: 15px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        
        .stat-item {{
            text-align: center;
        }}
        
        .stat-value {{
            font-size: 1.5em;
            font-weight: bold;
            color: #667eea;
        }}
        
        .stat-label {{
            font-size: 0.85em;
            color: #6c757d;
            margin-top: 5px;
        }}
    </style>
</head>
<body>
    <div class="dashboard-container">
        <div class="header">
            <h1>🚀 Enhanced Developer Analytics</h1>
            <div class="subtitle">AI-Powered Insights & Comprehensive Performance Analysis</div>
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
                <div class="value">{avg_business_impact:.1f}</div>
                <div class="label">Avg Business Impact</div>
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
                    {achievement_timeline}
                </div>
            </div>
            <div class="chart-grid">
                <div class="chart-container">
                    {weekly_trends}
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
            
            setTimeout(function() {{
                window.dispatchEvent(new Event('resize'));
            }}, 100);
        }}
        
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
        for summary in dashboard_data['developer_summaries']:
            achievements_html = ""
            if summary['achievements']:
                for achievement in summary['achievements']:
                    achievements_html += f"<li>{achievement}</li>"
            else:
                achievements_html = "<li>Recent development work completed</li>"
            
            features_html = ", ".join(summary['key_features'][:3]) if summary['key_features'] else "Various development tasks"
            
            summaries_html += f'''
            <div class="developer-summary">
                <div class="developer-name">{summary['developer']}</div>
                <div><strong>Period:</strong> {summary['period_start']} to {summary['period_end']}</div>
                <div><strong>Key Work:</strong> {features_html}</div>
                <div><strong>Quality Trend:</strong> {summary['quality_trend']}</div>
                <div><strong>Technical Depth:</strong> {summary['technical_depth']}</div>
                
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-value">{summary['stats']['total_commits']}</div>
                        <div class="stat-label">Commits</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{summary['stats']['avg_quality']}</div>
                        <div class="stat-label">Avg Quality</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{summary['stats']['avg_business_impact']}</div>
                        <div class="stat-label">Business Impact</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{summary['stats']['lines_changed']:,}</div>
                        <div class="stat-label">Lines Changed</div>
                    </div>
                </div>
                
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
            avg_business_impact=stats['avg_business_impact'],
            high_impact_commits=stats['high_impact_commits'],
            performance_radar=charts['performance_radar'].to_html(include_plotlyjs=False, full_html=False),
            impact_vs_quality=charts['impact_vs_quality'].to_html(include_plotlyjs=False, full_html=False),
            performance_matrix=charts['performance_matrix'].to_html(include_plotlyjs=False, full_html=False),
            feature_distribution=charts['feature_distribution'].to_html(include_plotlyjs=False, full_html=False),
            risk_distribution=charts['risk_distribution'].to_html(include_plotlyjs=False, full_html=False),
            complexity_trends=charts['complexity_trends'].to_html(include_plotlyjs=False, full_html=False),
            achievement_timeline=charts['achievement_timeline'].to_html(include_plotlyjs=False, full_html=False),
            weekly_trends=charts['weekly_trends'].to_html(include_plotlyjs=False, full_html=False),
            developer_summaries_html=summaries_html
        )

async def main():
    """Main function to generate enhanced dashboard"""
    generator = FixedEnhancedDashboardGenerator()
    await generator.create_enhanced_dashboard()

if __name__ == '__main__':
    asyncio.run(main())