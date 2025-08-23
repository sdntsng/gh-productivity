# GitHub Productivity Analytics Configuration
# Copy this file to config.py and customize the values below

# GitHub API Configuration
GITHUB_TOKEN = ""  # Your GitHub personal access token
ORG_NAME = ""      # Your GitHub organization name

# Data Collection Settings
INCLUDE_PRIVATE = True      # Include private repositories
EXCLUDE_ARCHIVED = True     # Exclude archived repositories  
INCLUDE_STATS = True        # Include detailed line count statistics (slower but more comprehensive)
SHOW_REPO_LIST = True       # Print repository list during processing
SHOW_PROGRESS = True        # Show progress messages during processing

# Author Management - Customize for your team
CORE_TEAM = [
    "developer1",
    "developer2", 
    "developer3",
    "Team Bot"
]

# Author name mapping for deduplication (maps variations to canonical names)
AUTHOR_MAPPING = {
    "dev1@company.com": "developer1",
    "Developer One": "developer1",
    "dev2-laptop": "developer2",
    # Add more mappings as needed
}

# External contributors to exclude from core team analysis
EXTERNAL_CONTRIBUTORS = {
    "dependabot[bot]",
    "github-actions[bot]",
    "renovate[bot]",
    "external-contributor1",
    # Add more external contributors as needed
}

# Commit Quality Scoring Configuration
QUALITY_WEIGHTS = {
    'has_issue_ref': 2.0,        # References issue/ticket
    'follows_convention': 1.5,    # Follows conventional commit format
    'good_length': 1.0,          # Appropriate message length
    'has_body': 0.5,             # Has commit body/description
    'not_merge': 0.5,            # Not a merge commit
    'not_hotfix': -0.5           # Penalty for hotfix commits
}

# Message length thresholds for quality scoring
MIN_MESSAGE_LENGTH = 10
MAX_MESSAGE_LENGTH = 72
IDEAL_MESSAGE_LENGTH = 50

# Working Hours Analysis
WORK_START_HOUR = 9    # Business hours start (24h format)
WORK_END_HOUR = 18     # Business hours end (24h format)

# Output File Configuration
COMMIT_ANALYSIS_FILE = "commit_analysis.csv"
PRODUCTIVITY_FILE = "developer_productivity.csv"
DASHBOARD_FILE = "productivity_dashboard.html"

# LLM Analysis Settings
GEMINI_API_KEY = ""  # Add your Gemini API key here
GEMINI_MODEL = "gemini-pro"
ENABLE_LLM_ANALYSIS = False     # Enable LLM-powered commit analysis
LLM_BATCH_SIZE = 10            # Number of commits to analyze in one LLM call
LLM_ANALYSIS_CACHE_DAYS = 7    # Days to cache LLM analysis results

# Feature Flags
ENABLE_DETAILED_STATS = True    # Fetch detailed commit statistics (lines added/deleted)
ENABLE_QUALITY_ANALYSIS = True  # Perform commit message quality analysis
ENABLE_AUTHOR_MAPPING = True    # Apply author name deduplication
ENABLE_EXTERNAL_FILTERING = True # Filter out external contributors
ENABLE_WEEKLY_TRENDS = True     # Generate week-on-week trend analysis
ENABLE_WORKING_HOURS = True     # Analyze working hour patterns
ENABLE_REPOSITORY_STATS = True  # Include repository-level statistics

# Debugging & Logging
DEBUG_MODE = False              # Enable verbose debugging output
SHOW_REPO_LIST = True           # Print list of repositories being processed
SHOW_PROGRESS = True            # Show progress during analysis
