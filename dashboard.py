import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import numpy as np

class ProductivityDashboard:
    def __init__(self, commits_file, productivity_file):
        self.commits_df = pd.read_csv(commits_file)
        self.productivity_df = pd.read_csv(productivity_file)
        self.commits_df['date'] = pd.to_datetime(self.commits_df['date'])
        
    def create_quality_report(self):
        """Generate comprehensive quality report"""
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('Developer Productivity & Quality Analysis', fontsize=16)
        
        # 1. Quality Score Distribution
        axes[0,0].hist(self.productivity_df['avg_quality_score'], bins=20, alpha=0.7, color='skyblue')
        axes[0,0].set_title('Quality Score Distribution')
        axes[0,0].set_xlabel('Average Quality Score')
        axes[0,0].set_ylabel('Number of Developers')
        
        # 2. Top Performers
        top_performers = self.productivity_df.nlargest(10, 'avg_quality_score')
        axes[0,1].barh(top_performers['developer'], top_performers['avg_quality_score'])
        axes[0,1].set_title('Top 10 Developers by Quality Score')
        axes[0,1].set_xlabel('Quality Score')
        
        # 3. Commit Volume vs Quality
        axes[0,2].scatter(self.productivity_df['total_commits'], 
                         self.productivity_df['avg_quality_score'], 
                         alpha=0.6)
        axes[0,2].set_title('Commit Volume vs Quality')
        axes[0,2].set_xlabel('Total Commits')
        axes[0,2].set_ylabel('Average Quality Score')
        
        # 4. Conventional Commits Adoption
        axes[1,0].hist(self.productivity_df['conventional_rate'], bins=15, alpha=0.7, color='lightgreen')
        axes[1,0].set_title('Conventional Commits Adoption Rate')
        axes[1,0].set_xlabel('Adoption Rate (%)')
        axes[1,0].set_ylabel('Number of Developers')
        
        # 5. Issue Reference Rate
        axes[1,1].boxplot([self.productivity_df['issue_ref_rate']])
        axes[1,1].set_title('Issue Reference Rate Distribution')
        axes[1,1].set_ylabel('Reference Rate (%)')
        
        # 6. Activity Patterns
        daily_commits = self.commits_df.groupby(self.commits_df['date'].dt.date).size()
        axes[1,2].plot(daily_commits.index, daily_commits.values)
        axes[1,2].set_title('Daily Commit Activity')
        axes[1,2].set_xlabel('Date')
        axes[1,2].set_ylabel('Number of Commits')
        axes[1,2].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig('productivity_dashboard.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def generate_team_insights(self):
        """Generate team-level insights"""
        insights = {
            'team_size': len(self.productivity_df),
            'avg_team_quality': self.productivity_df['avg_quality_score'].mean(),
            'total_commits': self.productivity_df['total_commits'].sum(),
            'top_contributor': self.productivity_df.loc[
                self.productivity_df['total_commits'].idxmax(), 'developer'
            ],
            'quality_leader': self.productivity_df.loc[
                self.productivity_df['avg_quality_score'].idxmax(), 'developer'
            ],
            'conventional_adoption': self.productivity_df['conventional_rate'].mean(),
            'issue_tracking': self.productivity_df['issue_ref_rate'].mean(),
        }
        
        # Risk indicators
        high_revert_rate = self.productivity_df[self.productivity_df['revert_rate'] > 5]
        large_commit_concern = self.productivity_df[self.productivity_df['large_commit_rate'] > 30]
        low_quality = self.productivity_df[self.productivity_df['avg_quality_score'] < 4]
        
        return insights, {
            'high_revert_developers': high_revert_rate['developer'].tolist(),
            'large_commit_developers': large_commit_concern['developer'].tolist(),
            'quality_improvement_needed': low_quality['developer'].tolist()
        }
    
    def create_individual_reports(self):
        """Create individual developer reports"""
        reports = {}
        
        for _, dev in self.productivity_df.iterrows():
            dev_commits = self.commits_df[self.commits_df['author'] == dev['developer']]
            
            report = {
                'summary': {
                    'total_commits': dev['total_commits'],
                    'quality_score': dev['avg_quality_score'],
                    'rank_quality': (self.productivity_df['avg_quality_score'] > dev['avg_quality_score']).sum() + 1,
                    'rank_volume': (self.productivity_df['total_commits'] > dev['total_commits']).sum() + 1
                },
                'strengths': [],
                'improvement_areas': [],
                'commit_patterns': {
                    'avg_size': dev['avg_additions_per_commit'] + dev['avg_deletions_per_commit'],
                    'consistency': dev['commits_per_active_day'],
                    'recent_activity': len(dev_commits[dev_commits['date'] > datetime.now() - timedelta(days=7)])
                }
            }
            
            # Identify strengths
            if dev['avg_quality_score'] > self.productivity_df['avg_quality_score'].mean():
                report['strengths'].append('Above average commit message quality')
            if dev['conventional_rate'] > 80:
                report['strengths'].append('Excellent conventional commit adoption')
            if dev['issue_ref_rate'] > 60:
                report['strengths'].append('Good issue tracking practices')
            if dev['revert_rate'] < 2:
                report['strengths'].append('Low revert rate - stable code')
                
            # Identify improvement areas
            if dev['avg_quality_score'] < 5:
                report['improvement_areas'].append('Commit message quality needs improvement')
            if dev['conventional_rate'] < 30:
                report['improvement_areas'].append('Consider adopting conventional commit format')
            if dev['large_commit_rate'] > 25:
                report['improvement_areas'].append('Break down large commits into smaller, atomic changes')
            if dev['issue_ref_rate'] < 30:
                report['improvement_areas'].append('Improve issue tracking by referencing tickets in commits')
                
            reports[dev['developer']] = report
        
        return reports
    
    def export_executive_summary(self):
        """Create executive summary report"""
        insights, risks = self.generate_team_insights()
        
        summary = f"""
# Developer Productivity Executive Summary
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Team Overview
- Team Size: {insights['team_size']} developers
- Total Commits Analyzed: {insights['total_commits']:,}
- Average Quality Score: {insights['avg_team_quality']:.2f}/10

## Key Performance Indicators
- Top Contributor: {insights['top_contributor']} ({self.productivity_df.loc[self.productivity_df['developer'] == insights['top_contributor'], 'total_commits'].iloc[0]} commits)
- Quality Leader: {insights['quality_leader']} ({self.productivity_df.loc[self.productivity_df['developer'] == insights['quality_leader'], 'avg_quality_score'].iloc[0]:.2f} score)
- Conventional Commits Adoption: {insights['conventional_adoption']:.1f}%
- Issue Tracking Rate: {insights['issue_tracking']:.1f}%

## Risk Areas Requiring Attention
"""
        
        if risks['high_revert_developers']:
            summary += f"- High Revert Rate: {', '.join(risks['high_revert_developers'])}\n"
        if risks['large_commit_developers']:
            summary += f"- Large Commit Concern: {', '.join(risks['large_commit_developers'])}\n"
        if risks['quality_improvement_needed']:
            summary += f"- Quality Improvement Needed: {', '.join(risks['quality_improvement_needed'])}\n"
            
        summary += """
## Recommendations
1. Implement conventional commit training for developers with <30% adoption
2. Establish code review guidelines for commits >500 lines
3. Improve issue tracking processes to increase reference rates
4. Recognition program for developers with consistently high quality scores
"""
        
        with open('executive_summary.md', 'w') as f:
            f.write(summary)
        
        return summary

# Usage
if __name__ == "__main__":
    dashboard = ProductivityDashboard('commit_analysis.csv', 'developer_productivity.csv')
    
    # Generate visualizations
    dashboard.create_quality_report()
    
    # Get insights
    insights, risks = dashboard.generate_team_insights()
    print("Team Insights:", insights)
    print("Risk Areas:", risks)
    
    # Create individual reports
    individual_reports = dashboard.create_individual_reports()
    
    # Export executive summary
    exec_summary = dashboard.export_executive_summary()
    print("\nExecutive Summary saved to executive_summary.md")