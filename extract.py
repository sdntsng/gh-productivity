import os
import subprocess
import shutil
import requests
import pandas as pd
import json
from datetime import datetime, timedelta, timezone
import re
from collections import defaultdict
import config  # Import our configuration

class GitHubAnalyzer:
    def __init__(self, token=None, org_name=None):
        # Use config values as defaults, allow override
        self.token = token or config.GITHUB_TOKEN
        self.org_name = org_name or config.ORG_NAME
        self.headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.base_url = 'https://api.github.com'
        
        # Load configuration
        self.author_mapping = config.AUTHOR_MAPPING
        self.excluded_authors = config.EXCLUDED_AUTHORS
    
    def get_repos(self, include_private=True, exclude_archived=True):
        """Get repositories in the organization, optionally including private repos."""
        repos = []
        page = 1

        # Primary: list org repos (should include private with proper scopes)
        while True:
            url = f"{self.base_url}/orgs/{self.org_name}/repos"
            params = {'page': page, 'per_page': 100, 'type': 'all'}

            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code != 200:
                try:
                    err = response.json()
                except Exception:
                    err = {'message': response.text}
                print(f"Failed to fetch repos (status {response.status_code}): {err}")
                break

            page_repos = response.json()
            if not page_repos:
                break

            repos.extend(page_repos)
            page += 1

        # Fallback: fetch user repos by affiliation and filter by org owner
        if include_private:
            page = 1
            while True:
                url = f"{self.base_url}/user/repos"
                params = {'page': page, 'per_page': 100, 'affiliation': 'organization_member,owner', 'visibility': 'all'}
                resp = requests.get(url, headers=self.headers, params=params)
                if resp.status_code != 200:
                    break
                page_repos = resp.json()
                if not page_repos:
                    break
                # Filter to this org
                for r in page_repos:
                    if r.get('owner', {}).get('login') == self.org_name:
                        repos.append(r)
                page += 1

        # De-duplicate by full_name
        dedup = {}
        for r in repos:
            if exclude_archived and r.get('archived'):
                continue
            dedup[r.get('full_name', r.get('name'))] = r

        return list(dedup.values())
    
    def get_commits(self, repo_name, since_date=None, include_stats=None):
        """Get commits for a specific repository with optional detailed stats"""
        commits = []
        page = 1
        
        # Use config defaults if not specified
        if include_stats is None:
            include_stats = config.INCLUDE_STATS
        
        if since_date is None:
            # GitHub expects ISO8601 in UTC with Z suffix
            since_date = (datetime.now(timezone.utc) - timedelta(days=config.ANALYSIS_DAYS)).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
        
        while True:
            url = f"{self.base_url}/repos/{self.org_name}/{repo_name}/commits"
            params = {
                'page': page, 
                'per_page': 100,
                'since': since_date
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code != 200:
                try:
                    err = response.json()
                except Exception:
                    err = {'message': response.text}
                if config.DEBUG_MODE:
                    print(f"Failed to fetch commits for {repo_name} (status {response.status_code}): {err}")
                break
                
            page_commits = response.json()
            if not page_commits:
                break
            
            # Optionally fetch detailed stats for each commit (slower but accurate)
            if include_stats:
                for i, commit in enumerate(page_commits):
                    if i < config.MAX_COMMITS_PER_PAGE:  # Limit to avoid rate limits
                        try:
                            detail_url = f"{self.base_url}/repos/{self.org_name}/{repo_name}/commits/{commit['sha']}"
                            detail_response = requests.get(detail_url, headers=self.headers)
                            if detail_response.status_code == 200:
                                detailed = detail_response.json()
                                commit['stats'] = detailed.get('stats', {'additions': 0, 'deletions': 0, 'total': 0})
                            else:
                                commit['stats'] = {'additions': 0, 'deletions': 0, 'total': 0}
                        except Exception:
                            commit['stats'] = {'additions': 0, 'deletions': 0, 'total': 0}
                    else:
                        commit['stats'] = {'additions': 0, 'deletions': 0, 'total': 0}
                        
            commits.extend(page_commits)
            page += 1
            
        return commits
    
    def get_pull_requests(self, repo_name, state='all'):
        """Get pull requests for a repository"""
        prs = []
        page = 1
        
        while True:
            url = f"{self.base_url}/repos/{self.org_name}/{repo_name}/pulls"
            params = {
                'page': page, 
                'per_page': 100,
                'state': state
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code != 200:
                try:
                    err = response.json()
                except Exception:
                    err = {'message': response.text}
                print(f"Failed to fetch PRs for {repo_name} (status {response.status_code}): {err}")
                break
                
            page_prs = response.json()
            if not page_prs:
                break
                
            prs.extend(page_prs)
            page += 1
            
        return prs
    
    def normalize_author(self, author_name):
        """Normalize author names using mapping and exclude unwanted authors"""
        if author_name in self.excluded_authors:
            return None
        return self.author_mapping.get(author_name, author_name)
    
    def analyze_commit_messages(self, commits):
        """Analyze commit message quality with enhanced metrics"""
        analysis = []
        
        for commit in commits:
            message = commit['commit']['message']
            author = commit['commit']['author']['name']
            date = commit['commit']['author']['date']
            
            # Normalize author name
            normalized_author = self.normalize_author(author)
            if normalized_author is None:  # Skip excluded authors
                continue
            
            # Analyze message quality
            quality_score = self.score_commit_message(message)
            
            stats = commit.get('stats', {})
            
            analysis.append({
                'sha': commit['sha'],
                'author': normalized_author,
                'original_author': author,
                'date': date,
                'message': message,
                'quality_score': quality_score,
                'message_length': len(message),
                'has_issue_ref': bool(re.search(r'#\d+', message)),
                'follows_convention': self.follows_conventional_commits(message),
                'is_merge': message.startswith('Merge'),
                'is_revert': message.startswith('Revert'),
                'is_hotfix': 'hotfix' in message.lower() or 'urgent' in message.lower(),
                'additions': stats.get('additions', 0),
                'deletions': stats.get('deletions', 0),
                'total_changes': stats.get('total', 0),
                'commit_hour': pd.to_datetime(date).hour,
                'commit_weekday': pd.to_datetime(date).dayofweek,
                'message_words': len(message.split()),
                'has_breaking_change': 'BREAKING CHANGE' in message or ('!' in message.split(':')[0] if ':' in message else False)
            })
        
        return pd.DataFrame(analysis)
    
    def score_commit_message(self, message):
        """Score commit message quality (0-10)"""
        score = config.QUALITY_BASE_SCORE  # Base score from config
        
        # Length check
        if len(message) < config.QUALITY_MIN_LENGTH:
            score -= 2
        elif len(message) > config.QUALITY_GOOD_LENGTH:
            score += 1
            
        # Descriptiveness
        if any(word in message.lower() for word in config.VAGUE_WORDS):
            score -= 1
            
        # Issue reference
        if re.search(r'#\d+', message):
            score += 1
            
        # Conventional commits
        if self.follows_conventional_commits(message):
            score += 2
            
        # Capital first letter
        if message[0].isupper():
            score += 0.5
            
        return min(10, max(0, score))
    
    def follows_conventional_commits(self, message):
        """Check if message follows conventional commits format"""
        return bool(re.match(config.CONVENTIONAL_COMMIT_PATTERN, message))
    
    def analyze_developer_productivity(self, commits_df):
        """Analyze developer productivity metrics with enhanced data points"""
        developer_stats = defaultdict(lambda: {
            'total_commits': 0,
            'avg_quality_score': 0,
            'total_additions': 0,
            'total_deletions': 0,
            'total_changes': 0,
            'merge_commits': 0,
            'reverts': 0,
            'hotfixes': 0,
            'issue_references': 0,
            'conventional_commits': 0,
            'breaking_changes': 0,
            'commit_frequency': {},
            'large_commits': 0,
            'weekend_commits': 0,
            'late_night_commits': 0,  # 22-6
            'business_hours_commits': 0,  # 9-17
            'total_words_in_messages': 0,
            'productive_days': set()
        })
        
        for _, commit in commits_df.iterrows():
            author = commit['author']
            stats = developer_stats[author]
            
            stats['total_commits'] += 1
            stats['avg_quality_score'] += commit['quality_score']
            stats['total_additions'] += commit['additions']
            stats['total_deletions'] += commit['deletions']
            stats['total_changes'] += commit['total_changes']
            stats['total_words_in_messages'] += commit['message_words']
            
            if commit['is_merge']:
                stats['merge_commits'] += 1
            if commit['is_revert']:
                stats['reverts'] += 1
            if commit['is_hotfix']:
                stats['hotfixes'] += 1
            if commit['has_issue_ref']:
                stats['issue_references'] += 1
            if commit['follows_convention']:
                stats['conventional_commits'] += 1
            if commit['has_breaking_change']:
                stats['breaking_changes'] += 1
            if commit['additions'] + commit['deletions'] > config.QUALITY_LARGE_COMMIT_THRESHOLD:
                stats['large_commits'] += 1
            
            # Time-based analysis
            hour = commit['commit_hour']
            weekday = commit['commit_weekday']
            
            if weekday in config.WEEKEND_DAYS:
                stats['weekend_commits'] += 1
            if hour >= config.LATE_NIGHT_START or hour <= config.LATE_NIGHT_END:
                stats['late_night_commits'] += 1
            if config.BUSINESS_HOURS_START <= hour <= config.BUSINESS_HOURS_END:
                stats['business_hours_commits'] += 1
                
            # Track commit frequency by day
            date = pd.to_datetime(commit['date']).date()
            stats['commit_frequency'][date] = stats['commit_frequency'].get(date, 0) + 1
            stats['productive_days'].add(date)
        
        # Calculate averages and percentages
        results = []
        for author, stats in developer_stats.items():
            if stats['total_commits'] > 0:
                results.append({
                    'developer': author,
                    'total_commits': stats['total_commits'],
                    'avg_quality_score': round(stats['avg_quality_score'] / stats['total_commits'], 2),
                    'total_lines_added': stats['total_additions'],
                    'total_lines_deleted': stats['total_deletions'],
                    'total_line_changes': stats['total_changes'],
                    'avg_lines_per_commit': round(stats['total_changes'] / stats['total_commits'], 2),
                    'avg_additions_per_commit': round(stats['total_additions'] / stats['total_commits'], 2),
                    'avg_deletions_per_commit': round(stats['total_deletions'] / stats['total_commits'], 2),
                    'merge_rate': round(stats['merge_commits'] / stats['total_commits'] * 100, 2),
                    'revert_rate': round(stats['reverts'] / stats['total_commits'] * 100, 2),
                    'hotfix_rate': round(stats['hotfixes'] / stats['total_commits'] * 100, 2),
                    'issue_ref_rate': round(stats['issue_references'] / stats['total_commits'] * 100, 2),
                    'conventional_rate': round(stats['conventional_commits'] / stats['total_commits'] * 100, 2),
                    'breaking_change_rate': round(stats['breaking_changes'] / stats['total_commits'] * 100, 2),
                    'large_commit_rate': round(stats['large_commits'] / stats['total_commits'] * 100, 2),
                    'weekend_commit_rate': round(stats['weekend_commits'] / stats['total_commits'] * 100, 2),
                    'late_night_commit_rate': round(stats['late_night_commits'] / stats['total_commits'] * 100, 2),
                    'business_hours_rate': round(stats['business_hours_commits'] / stats['total_commits'] * 100, 2),
                    'active_days': len(stats['commit_frequency']),
                    'productive_days': len(stats['productive_days']),
                    'commits_per_active_day': round(stats['total_commits'] / max(1, len(stats['commit_frequency'])), 2),
                    'avg_words_per_message': round(stats['total_words_in_messages'] / stats['total_commits'], 2),
                    'consistency_score': round(len(stats['productive_days']) / max(1, (max(stats['productive_days']) - min(stats['productive_days'])).days + 1) * 100, 2) if stats['productive_days'] else 0
                })
        
        return pd.DataFrame(results)

# Usage example
def main():
    # Use config values directly
    token = config.GITHUB_TOKEN
    org_name = config.ORG_NAME

    if not token:
        print("Error: GITHUB_TOKEN not set in config.py")
        print("Please copy config.example.py to config.py and set your GitHub token")
        return

    if not org_name:
        print("Error: ORG_NAME not set in config.py")
        print("Please copy config.example.py to config.py and set your organization name")
        return

    # Initialize analyzer
    analyzer = GitHubAnalyzer(token, org_name)
    
    # Get repositories
    print("Fetching repositories...")
    repos = analyzer.get_repos(
        include_private=config.INCLUDE_PRIVATE, 
        exclude_archived=config.EXCLUDE_ARCHIVED
    )

    # Debug: Check what we got
    if config.SHOW_REPO_LIST:
        print(f"Found {len(repos)} repositories:")
        for repo in repos:
            privacy = "private" if repo.get('private') else "public"
            print(f"  - {repo['name']} ({privacy})")

    # GitHub CLI fallback logic (keeping existing logic)
    private_count = sum(1 for r in repos if r.get('private'))
    if private_count == 0 and shutil.which('gh'):
        try:
            print("No private repos found, trying GitHub CLI directly...")
            env = os.environ.copy()
            env['GH_TOKEN'] = subprocess.check_output(['gh', 'auth', 'token'], text=True).strip()
            
            gh_output = subprocess.check_output(
                f'gh repo list {org_name} --json name,isPrivate,isArchived',
                shell=True, text=True, env=env
            ).strip()
            
            if gh_output:
                import json
                gh_repos = json.loads(gh_output)
                print(f"GitHub CLI found {len(gh_repos)} repos (including private)")
                
                if len(gh_repos) > len(repos):
                    gh_token = env['GH_TOKEN']
                    analyzer.token = gh_token
                    analyzer.headers['Authorization'] = f'token {gh_token}'
                    print("Updated analyzer to use GitHub CLI token")
                
                repos = []
                for gh_repo in gh_repos:
                    if config.EXCLUDE_ARCHIVED and gh_repo.get('isArchived'):
                        continue
                    
                    repos.append({
                        'name': gh_repo['name'],
                        'private': gh_repo.get('isPrivate', False),
                        'archived': gh_repo.get('isArchived', False),
                        'full_name': f"{org_name}/{gh_repo['name']}"
                    })
                
                print(f"Total repos after CLI replacement: {len(repos)}")
                        
        except Exception as e:
            print(f"GitHub CLI fallback failed: {e}")

    all_commits_data = []
    for repo in repos:
        repo_name = repo['name']
        if config.SHOW_PROGRESS:
            print(f"Processing {repo_name}...")
        
        # Get commits with stats based on config
        commits = analyzer.get_commits(repo_name)
        
        # Analyze commits
        if commits:
            commits_df = analyzer.analyze_commit_messages(commits)
            commits_df['repository'] = repo_name
            all_commits_data.append(commits_df)
    
    # Combine all commit data
    if all_commits_data:
        combined_commits = pd.concat(all_commits_data, ignore_index=True)
        
        # Analyze developer productivity
        productivity_df = analyzer.analyze_developer_productivity(combined_commits)
        
        # Save results using config file names
        combined_commits.to_csv(config.COMMIT_ANALYSIS_FILE, index=False)
        productivity_df.to_csv(config.PRODUCTIVITY_FILE, index=False)
        
        print(f"Analysis complete! Check {config.COMMIT_ANALYSIS_FILE} and {config.PRODUCTIVITY_FILE}")
        print("\nTop performers by quality score:")
        print(productivity_df.nlargest(10, 'avg_quality_score')[['developer', 'avg_quality_score', 'total_commits']])

if __name__ == "__main__":
    main()