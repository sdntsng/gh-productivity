# GitHub Productivity Analytics 🚀

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![GitHub issues](https://img.shields.io/github/issues/sdntsng/gh-productivity)](https://github.com/sdntsng/gh-productivity/issues)

**Tags:** `github-analytics` • `llm-powered` • `developer-productivity` • `team-metrics` • `ai-insights` • `gemini-api` • `code-analysis` • `git-insights` • `dashboard` • `plotly` • `data-visualization` • `commit-analysis` • `productivity-tracking` • `github-api` • `team-dashboard` • `developer-insights` • `github-stats` • `analytics`

> **Next-generation GitHub organization analytics with AI-powered insights and beautiful interactive dashboards for tracking developer productivity, commit quality, and team performance metrics.**

A powerful, AI-enhanced toolkit for analyzing GitHub organization activity and generating comprehensive productivity insights. Features LLM-powered commit analysis, developer performance summaries, comparative metrics, and changelog-style reporting that goes beyond traditional metrics to understand what developers actually build and achieve.

## Features

### 🤖 AI-Powered Analysis
- **LLM-Enhanced Commit Analysis**: Gemini API integration for intelligent commit assessment
- **Business Impact Scoring**: AI evaluation of actual business value delivered (0-10 scale)
- **Feature Type Classification**: Automatic categorization (feature/bugfix/refactoring/etc.)
- **Complexity Assessment**: AI-driven complexity analysis (low/medium/high/very_high)
- **Risk Level Detection**: Intelligent risk assessment for commits and changes
- **Learning Indicators**: AI detection of developer growth patterns and struggles

### 📊 Advanced Analytics & Metrics
- **Multi-Repository Analysis**: Analyze all repositories in your GitHub organization (public and private)
- **Comparative Developer Performance**: Percentile rankings and multi-dimensional comparisons
- **Traditional + AI Quality Scoring**: Both rule-based and LLM-powered quality assessment
- **Team Performance Benchmarking**: Advanced comparative metrics across time horizons
- **Developer Performance Radar**: Multi-dimensional performance visualization
- **Changelog-Style Summaries**: Semantic understanding of what developers actually built
- **Time-based Analysis**: Working hours patterns, weekly trends, productivity cycles

### 🎯 Enhanced Dashboard Experience
- **Performance Radar Charts**: Multi-dimensional developer comparison visualization
- **Business Impact vs Quality Scatter**: Advanced performance positioning analysis  
- **Feature Distribution Analysis**: Understanding of work type patterns by developer
- **Complexity Trends**: Track increasing sophistication of work over time
- **Achievement Timelines**: Changelog-style view of developer contributions and milestones
- **Risk Assessment Views**: Visual analysis of code risk patterns
- **Comparative Performance Matrix**: Heat-map style developer comparison across all metrics

### 🔧 Smart Features
- **Intelligent Caching**: LLM analysis results cached to minimize API costs
- **Batch Processing**: Efficient analysis of large commit volumes
- **Author Deduplication**: Intelligent mapping of multiple author identities
- **Team Filtering**: Focus on core team members, exclude bots and external contributors
- **Private Repository Support**: Full GitHub Enterprise and private org support
- **Configurable Scoring**: Customize both traditional and AI-powered quality metrics
- **Export Capabilities**: Enhanced CSV data export with AI insights
- **CI/CD Integration**: Automated reporting and monitoring with AI summaries

### 💻 Developer Experience
- **Easy Setup**: One-command configuration with guided LLM API setup
- **Cost-Effective**: Intelligent caching and batching to minimize LLM API costs
- **Multiple Dashboard Types**: Both traditional and AI-enhanced dashboard options
- **Extensible**: Plugin architecture for custom metrics and AI prompts
- **Well Documented**: Comprehensive guides including AI configuration
- **Open Source**: MIT licensed, community-driven development

## Dashboard Screenshots

### Traditional Dashboard
The standard dashboard (`web_dashboard.py`) includes:
- Weekly commit activity trends with filtering
- Quality score progression over time
- Lines of code metrics and repository heatmaps
- Working hours analysis and performance comparisons
- Time period filtering (last 7/30/90 days, quarters, etc.)

### AI-Enhanced Dashboard
The enhanced dashboard (`enhanced_dashboard.py`) features:
- **Performance Radar Charts**: Multi-dimensional developer comparison
- **Business Impact vs Quality Analysis**: AI-powered positioning of developers
- **Feature Distribution Charts**: Understanding what type of work each developer does
- **Complexity Trend Analysis**: Tracking sophistication of work over time
- **Achievement Timeline**: Changelog-style view of developer milestones
- **Risk Assessment Visualization**: Visual analysis of code risk patterns
- **Developer Summary Reports**: AI-generated performance summaries with key achievements

## Use Cases

### For Engineering Managers
- **AI-Powered Performance Reviews**: Get comprehensive, data-driven developer assessments
- **Business Impact Tracking**: Understand which developers deliver the most business value
- **Skill Gap Analysis**: AI detection of learning patterns and growth opportunities
- **Resource Planning**: Comparative analytics for sprint planning and task allocation
- **Quality Trend Analysis**: Monitor code quality improvements with traditional + AI metrics

### For Technical Leads
- **Mentoring Insights**: AI-generated developer summaries with specific growth recommendations
- **Code Review Optimization**: Risk assessment and complexity analysis for better reviews
- **Technical Debt Monitoring**: AI analysis of code complexity and maintenance burden
- **Knowledge Transfer**: Understanding who has expertise in different areas of the codebase
- **Architecture Decision Support**: Impact analysis of technical changes and initiatives

### For Development Teams
- **Personal Growth Tracking**: AI-powered analysis of your coding evolution and achievements
- **Comparative Benchmarking**: See how your performance compares within the team context
- **Learning Path Optimization**: AI recommendations for skill development priorities
- **Sprint Retrospective Data**: Rich analytics for team retrospectives and process improvement
- **Achievement Recognition**: Changelog-style summaries of your contributions and impact

### For Organizations
- **ROI Measurement**: Business impact scoring to measure development investment returns
- **Talent Assessment**: AI-powered evaluation for hiring, promotion, and team formation decisions
- **Process Optimization**: Data-driven insights for improving development workflows
- **Benchmark Establishment**: Comparative metrics for organizational performance standards
- **Strategic Planning**: Long-term trend analysis for technology and team investment decisions

## Installation

### Option 1: Using Conda (Recommended)

```bash
# Clone the repository
git clone https://github.com/sdntsng/gh-productivity.git
cd gh-productivity

# Create and activate conda environment
conda env create -f environment.yml
conda activate gh-productivity
```

### Option 2: Using pip

```bash
# Clone the repository
git clone https://github.com/sdntsng/gh-productivity.git
cd gh-productivity

# Install dependencies
pip install -r requirements.txt
```

## Configuration

### Quick Setup

1. **Run the setup script:**
   ```bash
   python setup.py
   ```
   This will create `config.py` from the example and guide you through the setup.

2. **Edit `config.py` with your settings:**
   ```python
   # GitHub API Configuration
   GITHUB_TOKEN = "your_github_token_here"
   ORG_NAME = "your_organization_name"
   
   # LLM Analysis Configuration (Optional but Recommended)
   GEMINI_API_KEY = "your_gemini_api_key_here"  # Get from Google AI Studio
   ENABLE_LLM_ANALYSIS = True  # Enable AI-powered insights
   
   # Core Team Members (customize for your team)
   CORE_TEAM = [
       "developer1",
       "developer2", 
       "developer3"
   ]
   
   # Add author mappings if team members use different names/emails
   AUTHOR_MAPPING = {
       "dev1@company.com": "developer1",
       "Developer One": "developer1",
   }
   ```

3. **Test your setup:**
   ```bash
   python test_setup.py
   ```
   This will verify that everything is configured correctly.

### Manual Configuration

If you prefer manual setup:

1. **Copy the example configuration file:**
   ```bash
   cp config.example.py config.py
   ```

2. **Generate API Keys:**
   
   **GitHub Personal Access Token:**
   - Go to GitHub Settings → Developer settings → Personal access tokens
   - Generate a token with these scopes: `repo`, `read:org`, `read:user`
   - For private repositories, ensure your token has appropriate access
   
   **Gemini API Key (Optional but Recommended):**
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key for Gemini Pro
   - This enables AI-powered commit analysis and developer insights

## Usage

### Step 1: Extract Data

```bash
python extract.py
```

This will:
- Fetch all repositories from your organization
- Analyze commit history and messages
- Generate `commit_analysis.csv` and `developer_productivity.csv`

### Step 2A: Generate Traditional Dashboard

```bash
python web_dashboard.py
```

Creates `productivity_dashboard.html` with time-series analysis, filtering, and traditional metrics.

### Step 2B: Generate AI-Enhanced Dashboard (Recommended)

```bash
python enhanced_dashboard.py
```

Creates `enhanced_dashboard.html` with:
- AI-powered commit analysis and business impact scoring
- Comparative performance radar charts
- Developer achievement summaries and changelog views
- Advanced risk assessment and complexity analysis

**Note:** Requires Gemini API key for full functionality. Falls back to traditional analysis if not configured.

### Optional: Static Charts

```bash
python dashboard.py
```

Generates `productivity_dashboard.png` with static matplotlib charts.

## What You Get

### CSV Outputs
- **`commit_analysis.csv`**: Detailed commit-level data with quality scores and AI insights
- **`developer_productivity.csv`**: Aggregated developer statistics and rankings
- **`llm_analysis_cache.json`**: Cached AI analysis results to minimize API costs

### Traditional Dashboard (`productivity_dashboard.html`)
- Weekly activity trends with developer filtering
- Commit quality progression over time with multiple time period views
- Lines of code statistics (additions, deletions, net changes)
- Repository activity heatmaps and working hours analysis
- Performance comparison tables with conditional formatting
- Mobile-responsive design with interactive charts

### Enhanced AI Dashboard (`enhanced_dashboard.html`)
- **Performance Radar Charts**: Multi-dimensional developer comparison across quality, productivity, and impact
- **Business Impact Analysis**: AI-scored business value positioning of each developer
- **Achievement Timelines**: Changelog-style visualization of developer milestones and contributions
- **Feature Distribution**: Understanding of work type patterns (features vs bugs vs refactoring)
- **Complexity Trend Analysis**: Tracking the sophistication of work over time
- **Risk Assessment**: Visual analysis of code risk patterns and quality concerns
- **Developer Summary Reports**: AI-generated performance summaries with specific achievements and growth recommendations

## Advanced Configuration

The `config.py` file offers extensive customization options:

### LLM Analysis Configuration
Control AI-powered analysis features:
```python
# Gemini API Configuration
GEMINI_API_KEY = "your_api_key_here"
GEMINI_MODEL = "gemini-pro"
ENABLE_LLM_ANALYSIS = True     # Enable AI-powered insights
LLM_BATCH_SIZE = 10            # Commits per batch (cost optimization)
LLM_ANALYSIS_CACHE_DAYS = 7    # Cache duration to minimize API costs
```

### Quality Scoring
Customize traditional quality scoring:
```python
QUALITY_BASE_SCORE = 5          # Starting score for all commits
QUALITY_MIN_LENGTH = 10         # Minimum characters for good message
QUALITY_GOOD_LENGTH = 50        # Characters for descriptive message bonus
VAGUE_WORDS = ['fix', 'update', 'change']  # Words that reduce quality score
CONVENTIONAL_COMMIT_PATTERN = r'^(feat|fix|docs|style|refactor|test|chore)(\(.+\))?: .+'
```

### Data Collection
Control what data is collected:
```python
INCLUDE_PRIVATE = True      # Include private repositories
EXCLUDE_ARCHIVED = True     # Exclude archived repositories  
INCLUDE_STATS = True        # Include detailed line count statistics
ANALYSIS_DAYS = 180         # Number of days to look back for commits
```

### Team Management
Filter and organize your team data:
```python
CORE_TEAM = ["dev1", "dev2", "dev3"]  # Your core team members

# Author name mapping for deduplication
AUTHOR_MAPPING = {
    'Samyak Gupta': 'samyaksgupta',
    'samyaksgupta': 'samyaksgupta',
    'dev@company.com': 'dev'
}

# External contributors to exclude
EXCLUDED_AUTHORS = {
    "github-actions[bot]",
    "dependabot[bot]",
    "external-contractor"
}
```

### Feature Flags
Enable/disable specific analysis features:
```python
ENABLE_LLM_ANALYSIS = True      # AI-powered commit analysis
ENABLE_WEEKLY_TRENDS = True     # Week-on-week trend analysis
ENABLE_WORKING_HOURS = True     # Working hour pattern analysis
ENABLE_REPOSITORY_STATS = True  # Repository-level statistics
ENABLE_QUALITY_ANALYSIS = True  # Commit message quality analysis
```

## Private Repository Access

For organizations with private repositories:

1. **Install GitHub CLI:**
   ```bash
   # macOS
   brew install gh
   
   # Other platforms: https://cli.github.com/
   ```

2. **Authenticate with GitHub CLI:**
   ```bash
   gh auth login
   ```

The tool will automatically use GitHub CLI for private repository access when needed.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Development Setup

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Make your changes and test thoroughly
4. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
5. Push to the branch (`git push origin feature/AmazingFeature`)
6. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Plotly](https://plotly.com/) for interactive visualizations
- Uses [pandas](https://pandas.pydata.org/) for data analysis
- GitHub API integration with fallback to [GitHub CLI](https://cli.github.com/)

## Support

If you encounter any issues or have questions:

1. Check the [Issues](../../issues) page for existing solutions
2. Create a new issue with detailed information about your problem
3. Include your configuration (without sensitive tokens) and error messages

---

Made with care for developer productivity insights
