#!/usr/bin/env python3
"""
Generate developer_productivity.csv from existing commit_analysis.csv
This is a standalone script that doesn't require external dependencies
"""

import csv
from collections import defaultdict
from datetime import datetime

def generate_productivity_csv():
    """Generate developer productivity summary from commit analysis data"""
    
    # Read commit analysis data
    commits = []
    try:
        with open('commit_analysis.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            commits = list(reader)
    except FileNotFoundError:
        print("Error: commit_analysis.csv not found")
        return
    
    # Aggregate by developer
    dev_stats = defaultdict(lambda: {
        'total_commits': 0,
        'total_additions': 0,
        'total_deletions': 0,
        'total_changes': 0,
        'quality_scores': [],
        'issue_refs': 0,
        'conventional_commits': 0,
        'merges': 0,
        'reverts': 0,
        'hotfixes': 0,
        'breaking_changes': 0,
        'repositories': set()
    })
    
    for commit in commits:
        author = commit['author']
        stats = dev_stats[author]
        
        stats['total_commits'] += 1
        stats['total_additions'] += int(commit['additions'] or 0)
        stats['total_deletions'] += int(commit['deletions'] or 0)
        stats['total_changes'] += int(commit['total_changes'] or 0)
        stats['quality_scores'].append(float(commit['quality_score'] or 0))
        stats['repositories'].add(commit['repository'])
        
        # Boolean fields
        if commit['has_issue_ref'] == 'TRUE':
            stats['issue_refs'] += 1
        if commit['follows_convention'] == 'TRUE':
            stats['conventional_commits'] += 1
        if commit['is_merge'] == 'TRUE':
            stats['merges'] += 1
        if commit['is_revert'] == 'TRUE':
            stats['reverts'] += 1
        if commit['is_hotfix'] == 'TRUE':
            stats['hotfixes'] += 1
        if commit['has_breaking_change'] == 'TRUE':
            stats['breaking_changes'] += 1
    
    # Write productivity summary
    with open('developer_productivity.csv', 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'developer', 'total_commits', 'avg_quality_score', 'total_lines_added',
            'total_lines_deleted', 'lines_changed', 'repositories_count',
            'issue_ref_rate', 'conventional_rate', 'merge_rate', 'revert_rate',
            'hotfix_rate', 'breaking_change_rate', 'avg_lines_per_commit'
        ]
        
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for developer, stats in dev_stats.items():
            if stats['total_commits'] == 0:
                continue
                
            avg_quality = sum(stats['quality_scores']) / len(stats['quality_scores'])
            
            writer.writerow({
                'developer': developer,
                'total_commits': stats['total_commits'],
                'avg_quality_score': round(avg_quality, 2),
                'total_lines_added': stats['total_additions'],
                'total_lines_deleted': stats['total_deletions'],
                'lines_changed': stats['total_changes'],
                'repositories_count': len(stats['repositories']),
                'issue_ref_rate': round(stats['issue_refs'] / stats['total_commits'] * 100, 1),
                'conventional_rate': round(stats['conventional_commits'] / stats['total_commits'] * 100, 1),
                'merge_rate': round(stats['merges'] / stats['total_commits'] * 100, 1),
                'revert_rate': round(stats['reverts'] / stats['total_commits'] * 100, 1),
                'hotfix_rate': round(stats['hotfixes'] / stats['total_commits'] * 100, 1),
                'breaking_change_rate': round(stats['breaking_changes'] / stats['total_commits'] * 100, 1),
                'avg_lines_per_commit': round(stats['total_changes'] / stats['total_commits'], 1)
            })
    
    print(f"Generated developer_productivity.csv with {len(dev_stats)} developers")
    
    # Print summary
    for developer, stats in sorted(dev_stats.items(), key=lambda x: x[1]['total_commits'], reverse=True):
        avg_quality = sum(stats['quality_scores']) / len(stats['quality_scores'])
        print(f"  {developer}: {stats['total_commits']} commits, {avg_quality:.1f} avg quality, {stats['total_changes']} lines changed")

if __name__ == '__main__':
    generate_productivity_csv()