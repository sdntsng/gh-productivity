import json
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import pandas as pd
import requests
import config

@dataclass
class CommitAnalysis:
    """Enhanced commit analysis with LLM insights"""
    sha: str
    author: str
    repository: str
    date: str
    message: str
    
    # Traditional metrics
    quality_score: float
    additions: int
    deletions: int
    total_changes: int
    
    # LLM-enhanced metrics
    llm_quality_score: float = 0.0
    business_impact_score: float = 0.0
    feature_type: str = ""
    complexity_level: str = ""
    code_areas: List[str] = None
    key_changes: List[str] = None
    risk_level: str = ""
    learning_indicators: List[str] = None
    
    def __post_init__(self):
        if self.code_areas is None:
            self.code_areas = []
        if self.key_changes is None:
            self.key_changes = []
        if self.learning_indicators is None:
            self.learning_indicators = []

@dataclass
class DeveloperPeriodSummary:
    """Developer performance summary for a time period"""
    developer: str
    period_start: str
    period_end: str
    
    # Feature delivery summary
    features_completed: List[str] = None
    bugs_fixed: List[str] = None
    refactoring_done: List[str] = None
    
    # LLM insights
    overall_quality_trend: str = ""
    key_achievements: List[str] = None
    growth_areas: List[str] = None
    collaboration_quality: str = ""
    technical_depth: str = ""
    
    def __post_init__(self):
        if self.features_completed is None:
            self.features_completed = []
        if self.bugs_fixed is None:
            self.bugs_fixed = []
        if self.refactoring_done is None:
            self.refactoring_done = []
        if self.key_achievements is None:
            self.key_achievements = []
        if self.growth_areas is None:
            self.growth_areas = []

class LLMCommitAnalyzer:
    """LLM-powered commit analysis using Gemini"""
    
    def __init__(self):
        self.api_key = config.GEMINI_API_KEY
        self.model = config.GEMINI_MODEL
        self.cache = {}
        self.cache_file = "llm_analysis_cache.json"
        self.load_cache()
        
    def load_cache(self):
        """Load analysis cache from disk"""
        try:
            with open(self.cache_file, 'r') as f:
                self.cache = json.load(f)
        except FileNotFoundError:
            self.cache = {}
    
    def save_cache(self):
        """Save analysis cache to disk"""
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f)
    
    def get_cache_key(self, commit_data: Dict) -> str:
        """Generate cache key for commit analysis"""
        key_data = f"{commit_data['sha']}_{commit_data['message']}_{commit_data['diff'][:200]}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def is_cache_valid(self, timestamp: str) -> bool:
        """Check if cached analysis is still valid"""
        try:
            cache_date = datetime.fromisoformat(timestamp)
            return datetime.now() - cache_date < timedelta(days=config.LLM_ANALYSIS_CACHE_DAYS)
        except:
            return False
    
    async def analyze_commits_batch(self, commits_data: List[Dict]) -> List[CommitAnalysis]:
        """Analyze a batch of commits with LLM"""
        if not config.ENABLE_LLM_ANALYSIS or not self.api_key:
            return self._create_basic_analysis(commits_data)
        
        results = []
        for commit_data in commits_data:
            cache_key = self.get_cache_key(commit_data)
            
            # Check cache first
            if (cache_key in self.cache and 
                self.is_cache_valid(self.cache[cache_key].get('timestamp', ''))):
                analysis = CommitAnalysis(**self.cache[cache_key]['analysis'])
                results.append(analysis)
                continue
            
            # Perform LLM analysis
            try:
                llm_insights = await self._call_gemini_api(commit_data)
                analysis = self._create_enhanced_analysis(commit_data, llm_insights)
                
                # Cache the result
                self.cache[cache_key] = {
                    'analysis': asdict(analysis),
                    'timestamp': datetime.now().isoformat()
                }
                results.append(analysis)
                
            except Exception as e:
                print(f"LLM analysis failed for commit {commit_data['sha'][:7]}: {e}")
                analysis = self._create_basic_analysis([commit_data])[0]
                results.append(analysis)
        
        self.save_cache()
        return results
    
    async def _call_gemini_api(self, commit_data: Dict) -> Dict:
        """Call Gemini API for commit analysis"""
        prompt = self._build_analysis_prompt(commit_data)
        
        headers = {
            'Content-Type': 'application/json',
            'x-goog-api-key': self.api_key
        }
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 1000
            }
        }
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        content = result['candidates'][0]['content']['parts'][0]['text']
        
        # Parse JSON response
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Fallback parsing if JSON is malformed
            return self._parse_llm_response_fallback(content)
    
    def _build_analysis_prompt(self, commit_data: Dict) -> str:
        """Build analysis prompt for Gemini"""
        return f"""
Analyze this software commit and provide insights in JSON format:

COMMIT INFO:
SHA: {commit_data['sha']}
Author: {commit_data['author']}
Repository: {commit_data['repository']}
Message: {commit_data['message']}
Files Changed: {commit_data.get('files_changed', 'N/A')}
Lines Added: {commit_data.get('additions', 0)}
Lines Deleted: {commit_data.get('deletions', 0)}

CODE DIFF:
{commit_data.get('diff', 'No diff available')[:2000]}

Provide analysis in this exact JSON format:
{{
    "llm_quality_score": 0-10,
    "business_impact_score": 0-10,
    "feature_type": "feature|bugfix|refactoring|documentation|testing|maintenance",
    "complexity_level": "low|medium|high|very_high",
    "code_areas": ["specific areas of codebase affected"],
    "key_changes": ["3-5 most important changes made"],
    "risk_level": "low|medium|high",
    "learning_indicators": ["signs of developer growth or struggle"]
}}

Focus on:
1. Technical quality and maintainability
2. Business value and user impact
3. Code complexity appropriateness
4. Risk factors and potential issues
5. Developer skill demonstration
"""
    
    def _parse_llm_response_fallback(self, content: str) -> Dict:
        """Fallback parsing for malformed JSON responses"""
        return {
            "llm_quality_score": 6.0,
            "business_impact_score": 5.0,
            "feature_type": "maintenance",
            "complexity_level": "medium",
            "code_areas": ["general"],
            "key_changes": ["code changes"],
            "risk_level": "low",
            "learning_indicators": []
        }
    
    def _create_basic_analysis(self, commits_data: List[Dict]) -> List[CommitAnalysis]:
        """Create basic analysis without LLM enhancement"""
        results = []
        for commit_data in commits_data:
            analysis = CommitAnalysis(
                sha=commit_data['sha'],
                author=commit_data['author'],
                repository=commit_data['repository'],
                date=commit_data['date'],
                message=commit_data['message'],
                quality_score=commit_data.get('quality_score', 5.0),
                additions=commit_data.get('additions', 0),
                deletions=commit_data.get('deletions', 0),
                total_changes=commit_data.get('total_changes', 0)
            )
            results.append(analysis)
        return results
    
    def _create_enhanced_analysis(self, commit_data: Dict, llm_insights: Dict) -> CommitAnalysis:
        """Create enhanced analysis with LLM insights"""
        return CommitAnalysis(
            sha=commit_data['sha'],
            author=commit_data['author'],
            repository=commit_data['repository'],
            date=commit_data['date'],
            message=commit_data['message'],
            quality_score=commit_data.get('quality_score', 5.0),
            additions=commit_data.get('additions', 0),
            deletions=commit_data.get('deletions', 0),
            total_changes=commit_data.get('total_changes', 0),
            llm_quality_score=llm_insights.get('llm_quality_score', 6.0),
            business_impact_score=llm_insights.get('business_impact_score', 5.0),
            feature_type=llm_insights.get('feature_type', 'maintenance'),
            complexity_level=llm_insights.get('complexity_level', 'medium'),
            code_areas=llm_insights.get('code_areas', []),
            key_changes=llm_insights.get('key_changes', []),
            risk_level=llm_insights.get('risk_level', 'low'),
            learning_indicators=llm_insights.get('learning_indicators', [])
        )

class DeveloperSummaryGenerator:
    """Generate developer performance summaries using LLM analysis"""
    
    def __init__(self, llm_analyzer: LLMCommitAnalyzer):
        self.llm_analyzer = llm_analyzer
    
    def generate_period_summaries(self, 
                                analyses: List[CommitAnalysis], 
                                period_days: int = 7) -> List[DeveloperPeriodSummary]:
        """Generate periodic summaries for developers"""
        summaries = []
        
        # Group by developer and time period
        developer_periods = self._group_by_developer_period(analyses, period_days)
        
        for (developer, period_start, period_end), period_analyses in developer_periods.items():
            summary = self._create_period_summary(
                developer, period_start, period_end, period_analyses
            )
            summaries.append(summary)
        
        return summaries
    
    def _group_by_developer_period(self, 
                                 analyses: List[CommitAnalysis], 
                                 period_days: int) -> Dict:
        """Group analyses by developer and time period"""
        groups = {}
        
        for analysis in analyses:
            commit_date = datetime.fromisoformat(analysis.date.replace('Z', '+00:00'))
            
            # Calculate period boundaries
            days_since_epoch = (commit_date - datetime(1970, 1, 1, tzinfo=commit_date.tzinfo)).days
            period_number = days_since_epoch // period_days
            period_start = datetime(1970, 1, 1, tzinfo=commit_date.tzinfo) + timedelta(days=period_number * period_days)
            period_end = period_start + timedelta(days=period_days)
            
            key = (analysis.author, period_start.isoformat(), period_end.isoformat())
            
            if key not in groups:
                groups[key] = []
            groups[key].append(analysis)
        
        return groups
    
    def _create_period_summary(self, 
                             developer: str, 
                             period_start: str, 
                             period_end: str, 
                             analyses: List[CommitAnalysis]) -> DeveloperPeriodSummary:
        """Create summary for a developer's work in a period"""
        
        # Categorize work by feature type
        features = [a for a in analyses if a.feature_type == 'feature']
        bugs = [a for a in analyses if a.feature_type == 'bugfix']
        refactoring = [a for a in analyses if a.feature_type == 'refactoring']
        
        # Extract key changes
        features_completed = self._extract_key_work(features, 'features')
        bugs_fixed = self._extract_key_work(bugs, 'bug fixes')
        refactoring_done = self._extract_key_work(refactoring, 'refactoring')
        
        # Analyze quality trends
        quality_trend = self._analyze_quality_trend(analyses)
        
        # Extract achievements and growth areas
        key_achievements = self._extract_achievements(analyses)
        growth_areas = self._extract_growth_areas(analyses)
        
        return DeveloperPeriodSummary(
            developer=developer,
            period_start=period_start,
            period_end=period_end,
            features_completed=features_completed,
            bugs_fixed=bugs_fixed,
            refactoring_done=refactoring_done,
            overall_quality_trend=quality_trend,
            key_achievements=key_achievements,
            growth_areas=growth_areas,
            collaboration_quality=self._assess_collaboration_quality(analyses),
            technical_depth=self._assess_technical_depth(analyses)
        )
    
    def _extract_key_work(self, analyses: List[CommitAnalysis], work_type: str) -> List[str]:
        """Extract key work items from analyses"""
        work_items = []
        for analysis in analyses:
            if analysis.key_changes:
                work_items.extend(analysis.key_changes[:2])  # Top 2 changes per commit
        
        # Deduplicate and limit
        unique_work = list(dict.fromkeys(work_items))
        return unique_work[:5]  # Top 5 unique items
    
    def _analyze_quality_trend(self, analyses: List[CommitAnalysis]) -> str:
        """Analyze quality trend over the period"""
        if len(analyses) < 2:
            return "stable"
        
        scores = [a.llm_quality_score or a.quality_score for a in analyses]
        first_half = scores[:len(scores)//2]
        second_half = scores[len(scores)//2:]
        
        avg_first = sum(first_half) / len(first_half) if first_half else 0
        avg_second = sum(second_half) / len(second_half) if second_half else 0
        
        diff = avg_second - avg_first
        if diff > 0.5:
            return "improving"
        elif diff < -0.5:
            return "declining"
        else:
            return "stable"
    
    def _extract_achievements(self, analyses: List[CommitAnalysis]) -> List[str]:
        """Extract key achievements from the period"""
        achievements = []
        
        # High-impact work
        high_impact = [a for a in analyses if a.business_impact_score > 7]
        if high_impact:
            achievements.append(f"Delivered {len(high_impact)} high-impact changes")
        
        # Complex work
        complex_work = [a for a in analyses if a.complexity_level in ['high', 'very_high']]
        if complex_work:
            achievements.append(f"Successfully handled {len(complex_work)} complex tasks")
        
        # Quality work
        high_quality = [a for a in analyses if (a.llm_quality_score or a.quality_score) > 8]
        if len(high_quality) > len(analyses) * 0.6:
            achievements.append("Maintained consistently high code quality")
        
        return achievements[:3]  # Top 3 achievements
    
    def _extract_growth_areas(self, analyses: List[CommitAnalysis]) -> List[str]:
        """Extract growth areas from learning indicators"""
        growth_areas = []
        all_indicators = []
        
        for analysis in analyses:
            all_indicators.extend(analysis.learning_indicators)
        
        # Group similar indicators
        if any("test" in indicator.lower() for indicator in all_indicators):
            growth_areas.append("Testing practices")
        if any("document" in indicator.lower() for indicator in all_indicators):
            growth_areas.append("Documentation")
        if any("error" in indicator.lower() for indicator in all_indicators):
            growth_areas.append("Error handling")
        
        return growth_areas[:3]
    
    def _assess_collaboration_quality(self, analyses: List[CommitAnalysis]) -> str:
        """Assess collaboration quality based on commit patterns"""
        if not analyses:
            return "unknown"
        
        avg_quality = sum(a.llm_quality_score or a.quality_score for a in analyses) / len(analyses)
        
        if avg_quality > 7:
            return "excellent"
        elif avg_quality > 6:
            return "good"
        else:
            return "needs_improvement"
    
    def _assess_technical_depth(self, analyses: List[CommitAnalysis]) -> str:
        """Assess technical depth of work"""
        if not analyses:
            return "unknown"
        
        complex_ratio = len([a for a in analyses if a.complexity_level in ['high', 'very_high']]) / len(analyses)
        
        if complex_ratio > 0.4:
            return "deep"
        elif complex_ratio > 0.2:
            return "moderate"
        else:
            return "surface"