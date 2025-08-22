# � GitHub Productivity Analytics

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![GitHub issues](https://img.shields.io/github/issues/USER/REPO)](https://github.com/USER/REPO/issues)

**Tags:** `github-analytics` • `developer-productivity` • `team-metrics` • `code-analysis` • `git-insights` • `dashboard` • `plotly` • `data-visualization` • `commit-analysis` • `productivity-tracking` • `github-api` • `team-dashboard` • `developer-insights` • `github-stats` • `analytics`

> 📊 **Comprehensive GitHub organization analytics with beautiful interactive dashboards for tracking developer productivity, commit quality, and team performance metrics.**

A powerful toolkit for analyzing GitHub organization activity and generating interactive productivity insights dashboards. Track developer contributions, commit quality, weekly trends, and gain deep insights into your team's GitHub activity across all repositories.🚀 GitHub Productivity Analytics

A comprehensive toolkit for analyzing GitHub organization activity and generating interactive productivity insights dashboards. Track developer contributions, commit quality, weekly trends, and team productivity metrics across all your repositories.

## ✨ Features

### 📊 **Analytics & Metrics**
- **Multi-Repository Analysis**: Analyze all repositories in your GitHub organization (public and private)
- **Developer Productivity Tracking**: Monitor commits, code changes, quality scores, and working patterns
- **Commit Quality Scoring**: Automated analysis based on conventional commits, issue references, and message quality
- **Team Performance Metrics**: Compare developers, track trends, identify top performers
- **Code Metrics**: Lines added/deleted, file changes, repository activity patterns
- **Time-based Analysis**: Working hours patterns, weekly trends, productivity cycles

### 🎨 **Interactive Dashboards**
- **Web-based HTML Dashboards**: Beautiful interactive visualizations using Plotly
- **Weekly Trend Analysis**: Track productivity changes over time
- **Performance Comparisons**: Side-by-side developer and team comparisons  
- **Repository Heatmaps**: Visual activity patterns across projects
- **Quality Progression**: Monitor code quality improvements
- **Mobile-friendly**: Responsive design for viewing on any device

### 🔧 **Smart Features**
- **Author Deduplication**: Intelligent mapping of multiple author identities
- **Team Filtering**: Focus on core team members, exclude bots and external contributors
- **Private Repository Support**: Full GitHub Enterprise and private org support
- **Configurable Scoring**: Customize quality metrics for your team's standards
- **Export Capabilities**: CSV data export for further analysis
- **CI/CD Integration**: Automated reporting and monitoring

### 🚀 **Developer Experience**
- **Easy Setup**: One-command configuration with guided setup
- **Minimal Dependencies**: Lightweight Python stack with conda/pip support
- **Extensible**: Plugin architecture for custom metrics and visualizations
- **Well Documented**: Comprehensive guides and examples
- **Open Source**: MIT licensed, community-driven development

## 📊 Dashboard Screenshots

The generated dashboard includes:
- Weekly commit activity trends
- Quality score progression over time
- Lines of code metrics
- Repository activity heatmaps
- Working hours analysis
- Performance comparisons

## 🎯 Use Cases

### **For Engineering Managers**
- Track team productivity and identify bottlenecks
- Monitor code quality trends across projects
- Generate reports for stakeholders and leadership
- Identify training needs and skill gaps
- Plan resource allocation and sprint capacity

### **For Technical Leads**
- Code review insights and quality metrics
- Developer mentoring and performance feedback
- Repository health monitoring
- Technical debt identification
- Release planning and milestone tracking

### **For Development Teams**
- Personal productivity tracking and improvement
- Team collaboration insights
- Sprint retrospective data
- Working pattern optimization
- Knowledge sharing metrics

### **For Organizations**
- Engineering productivity benchmarking
- Remote work effectiveness measurement
- Hiring and onboarding insights
- Process improvement identification
- ROI measurement for development tools

## 🛠 Installation

### Option 1: Using Conda (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd gh-productivity

# Create and activate conda environment
conda env create -f environment.yml
conda activate gh-productivity
```

### Option 2: Using pip

```bash
# Clone the repository
git clone <repository-url>
cd gh-productivity

# Install dependencies
pip install -r requirements.txt
```

## ⚙️ Configuration

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

2. **Generate a GitHub Personal Access Token:**
   - Go to GitHub Settings → Developer settings → Personal access tokens
   - Generate a token with these scopes: `repo`, `read:org`, `read:user`
   - For private repositories, ensure your token has appropriate access

## 🚀 Usage

### Quick Start

1. **Initial setup:**
   ```bash
   python setup.py      # Set up configuration
   python test_setup.py # Verify everything works
   ```

2. **Run analysis:**
   ```bash
   python extract.py    # Extract data from GitHub
   python web_dashboard.py  # Generate dashboard
   ```

3. **View results:**
   Open `productivity_dashboard.html` in your browser for interactive insights!

### Detailed Steps

#### Step 1: Extract Data

```bash
python extract.py
```

This will:
- Fetch all repositories from your organization
- Analyze commit history and messages
- Generate `commit_analysis.csv` and `developer_productivity.csv`

### Step 2: Generate Dashboard

```bash
python web_dashboard.py
```

This creates `productivity_dashboard.html` - an interactive web dashboard you can open in your browser.

### Optional: Static Charts

```bash
python dashboard.py
```

Generates `productivity_dashboard.png` with static matplotlib charts.

## 📈 What You Get

### CSV Outputs
- **`commit_analysis.csv`**: Detailed commit-level data with quality scores
- **`developer_productivity.csv`**: Aggregated developer statistics and rankings

### Interactive Dashboard
- Weekly activity trends for each developer
- Commit quality progression over time
- Lines of code statistics (additions, deletions, net changes)
- Repository activity heatmaps
- Working hours pattern analysis
- Performance comparison charts

## 🔧 Advanced Configuration

The `config.py` file offers extensive customization options:

### Quality Scoring
Customize how commit quality is calculated:
```python
QUALITY_WEIGHTS = {
    'has_issue_ref': 2.0,        # References issue/ticket
    'follows_convention': 1.5,    # Follows conventional commit format
    'good_length': 1.0,          # Appropriate message length
    'has_body': 0.5,             # Has commit body/description
    'not_merge': 0.5,            # Not a merge commit
    'not_hotfix': -0.5           # Penalty for hotfix commits
}
```

### Data Collection
Control what data is collected:
```python
INCLUDE_PRIVATE = True      # Include private repositories
EXCLUDE_ARCHIVED = True     # Exclude archived repositories  
INCLUDE_STATS = True        # Include detailed line count statistics
```

### Team Management
Filter and organize your team data:
```python
CORE_TEAM = ["dev1", "dev2", "dev3"]  # Your core team members

EXTERNAL_CONTRIBUTORS = {              # Contributors to exclude
    "dependabot[bot]",
    "github-actions[bot]",
    "external-contractor"
}
```

## 🔐 Private Repository Access

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

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Development Setup

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Make your changes and test thoroughly
4. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
5. Push to the branch (`git push origin feature/AmazingFeature`)
6. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Plotly](https://plotly.com/) for interactive visualizations
- Uses [pandas](https://pandas.pydata.org/) for data analysis
- GitHub API integration with fallback to [GitHub CLI](https://cli.github.com/)

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Issues](../../issues) page for existing solutions
2. Create a new issue with detailed information about your problem
3. Include your configuration (without sensitive tokens) and error messages

---

Made with ❤️ for developer productivity insights
