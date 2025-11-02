"""Repository-wide code analysis and modernization system.

This module provides tools to analyze entire repositories, detect outdated patterns,
research best practices, and generate comprehensive modernization recommendations.
"""
from typing import Dict, List, Any, Optional
import os
from pathlib import Path
from .code_modernizer import CodeModernizer
from .web_search import get_search_manager
from .semantic_analyzer import SemanticAnalyzer


class RepoAnalyzer:
    """Analyzes entire repositories and provides modernization recommendations."""
    
    def __init__(self, workspace_dir: str):
        """Initialize the repository analyzer.
        
        Args:
            workspace_dir: Root directory of the repository
        """
        self.workspace_dir = Path(workspace_dir)
        self.web_search = get_search_manager()
        self.semantic_analyzer = SemanticAnalyzer(workspace_dir)
        self.modernizer = CodeModernizer(self.web_search, self.semantic_analyzer)
        
        self.supported_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', 
            '.rs', '.cpp', '.c', '.h', '.hpp', '.cs', '.rb', '.php'
        }
        
        self.skip_dirs = {
            'node_modules', '__pycache__', '.git', '.venv', 'venv',
            'env', 'dist', 'build', 'target', '.pytest_cache', '.mypy_cache'
        }
    
    def analyze_repository(self, max_files: int = 50, focus_paths: Optional[List[str]] = None) -> Dict[str, Any]:
        """Analyze entire repository and generate modernization recommendations.
        
        Args:
            max_files: Maximum number of files to analyze (prevents timeout)
            focus_paths: Optional list of specific paths to analyze
            
        Returns:
            Dictionary with analysis results, recommendations, and migration plan
        """
        print(f"🔍 Starting repository analysis: {self.workspace_dir}")
        
        # Step 1: Discover files
        files_to_analyze = self._discover_files(max_files, focus_paths)
        
        if not files_to_analyze:
            return {
                'ok': False,
                'error': 'No supported files found in repository',
                'workspace': str(self.workspace_dir)
            }
        
        print(f"📁 Found {len(files_to_analyze)} files to analyze")
        
        # Step 2: Analyze each file
        file_results = []
        total_patterns = 0
        severity_counts = {'high': 0, 'medium': 0, 'low': 0}
        
        for file_path in files_to_analyze:
            try:
                result = self._analyze_file(file_path)
                if result['ok'] and result.get('outdated_patterns'):
                    file_results.append(result)
                    total_patterns += len(result['outdated_patterns'])
                    
                    # Count severities
                    for pattern in result['outdated_patterns']:
                        severity = pattern.get('severity', 'medium')
                        severity_counts[severity] = severity_counts.get(severity, 0) + 1
                        
            except Exception as e:
                print(f"⚠️ Error analyzing {file_path}: {str(e)}")
                continue
        
        if not file_results:
            return {
                'ok': True,
                'message': 'No outdated patterns detected',
                'workspace': str(self.workspace_dir),
                'files_analyzed': len(files_to_analyze),
                'recommendations': []
            }
        
        # Step 3: Research best practices for common patterns
        print(f"🌐 Researching best practices for detected patterns...")
        best_practices = self._research_common_patterns(file_results)
        
        # Step 4: Generate aggregated recommendations
        recommendations = self._generate_repo_recommendations(file_results, best_practices)
        
        # Step 5: Create migration plan
        migration_plan = self._create_migration_plan(recommendations, severity_counts)
        
        return {
            'ok': True,
            'workspace': str(self.workspace_dir),
            'files_analyzed': len(files_to_analyze),
            'files_with_issues': len(file_results),
            'total_patterns': total_patterns,
            'severity_counts': severity_counts,
            'recommendations': recommendations[:20],  # Top 20 recommendations
            'migration_plan': migration_plan,
            'best_practices': best_practices
        }
    
    def _discover_files(self, max_files: int, focus_paths: Optional[List[str]]) -> List[Path]:
        """Discover files to analyze in the repository."""
        files = []
        
        if focus_paths:
            # Analyze only specified paths
            for path_str in focus_paths:
                path = self.workspace_dir / path_str
                if path.is_file() and path.suffix in self.supported_extensions:
                    files.append(path)
                elif path.is_dir():
                    files.extend(self._walk_directory(path, max_files - len(files)))
        else:
            # Analyze entire repository
            files = self._walk_directory(self.workspace_dir, max_files)
        
        return files[:max_files]
    
    def _walk_directory(self, directory: Path, max_files: int) -> List[Path]:
        """Walk directory and collect supported files."""
        files = []
        
        try:
            for item in directory.rglob('*'):
                if len(files) >= max_files:
                    break
                
                # Skip excluded directories
                if any(skip_dir in item.parts for skip_dir in self.skip_dirs):
                    continue
                
                # Check if it's a supported file
                if item.is_file() and item.suffix in self.supported_extensions:
                    files.append(item)
        except Exception as e:
            print(f"⚠️ Error walking directory {directory}: {str(e)}")
        
        return files
    
    def _analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a single file for outdated patterns."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            relative_path = str(file_path.relative_to(self.workspace_dir))
            
            result = self.modernizer.analyze_and_recommend(
                code=content,
                file_path=relative_path,
                language=None  # Auto-detect
            )
            
            if result.get('ok'):
                result['absolute_path'] = str(file_path)
                result['relative_path'] = relative_path
            
            return result
            
        except Exception as e:
            return {
                'ok': False,
                'error': str(e),
                'file_path': str(file_path)
            }
    
    def _research_common_patterns(self, file_results: List[Dict]) -> Dict[str, Any]:
        """Research best practices for commonly found patterns."""
        # Aggregate patterns across files
        pattern_counts = {}
        
        for result in file_results:
            for pattern in result.get('outdated_patterns', []):
                pattern_name = pattern.get('pattern', 'Unknown')
                if pattern_name not in pattern_counts:
                    pattern_counts[pattern_name] = {
                        'count': 0,
                        'severity': pattern.get('severity', 'medium'),
                        'files': []
                    }
                pattern_counts[pattern_name]['count'] += 1
                pattern_counts[pattern_name]['files'].append(result.get('relative_path'))
        
        # Research top 5 most common patterns
        top_patterns = sorted(pattern_counts.items(), key=lambda x: x[1]['count'], reverse=True)[:5]
        
        best_practices = {}
        for pattern_name, info in top_patterns:
            # Search for best practices
            query = f"modern alternative to {pattern_name} best practices 2024 2025"
            search_result = self.web_search.search(query, max_results=2)
            
            if search_result.get('ok') and search_result.get('results'):
                best_practices[pattern_name] = {
                    'count': info['count'],
                    'severity': info['severity'],
                    'affected_files': info['files'][:5],  # Show first 5 files
                    'resources': search_result['results']
                }
        
        return best_practices
    
    def _generate_repo_recommendations(self, file_results: List[Dict], best_practices: Dict) -> List[Dict]:
        """Generate aggregated recommendations for the repository."""
        recommendations = []
        
        # Group by severity
        for result in file_results:
            for rec in result.get('recommendations', []):
                recommendations.append({
                    'file': result.get('relative_path'),
                    'priority': rec.get('priority', 'medium'),
                    'title': rec.get('title'),
                    'description': rec.get('description'),
                    'alternative': rec.get('alternative'),
                    'example': rec.get('example'),
                    'effort': rec.get('effort', 'medium')
                })
        
        # Sort by priority: high > medium > low
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 1))
        
        return recommendations
    
    def _create_migration_plan(self, recommendations: List[Dict], severity_counts: Dict) -> Dict[str, Any]:
        """Create a step-by-step migration plan."""
        high_priority = [r for r in recommendations if r['priority'] == 'high']
        medium_priority = [r for r in recommendations if r['priority'] == 'medium']
        low_priority = [r for r in recommendations if r['priority'] == 'low']
        
        # Estimate effort
        total_items = len(recommendations)
        estimated_hours = (
            len(high_priority) * 2 +  # 2 hours per high priority
            len(medium_priority) * 1 +  # 1 hour per medium priority
            len(low_priority) * 0.5  # 30 min per low priority
        )
        
        return {
            'total_recommendations': total_items,
            'estimated_time': f"{int(estimated_hours)} hours" if estimated_hours > 1 else f"{int(estimated_hours * 60)} minutes",
            'difficulty': 'high' if severity_counts.get('high', 0) > 5 else 'medium' if severity_counts.get('medium', 0) > 10 else 'low',
            'steps': [
                {
                    'step': 1,
                    'title': 'Create backup branch',
                    'description': 'Create a new branch for modernization work',
                    'command': 'git checkout -b modernize-repo'
                },
                {
                    'step': 2,
                    'title': f'Fix critical issues ({len(high_priority)} items)',
                    'description': 'Address high-priority patterns first',
                    'items': [r['title'] for r in high_priority[:5]]
                },
                {
                    'step': 3,
                    'title': 'Update dependencies',
                    'description': 'Update package managers and dependencies',
                    'command': 'Check package.json, requirements.txt, go.mod, etc.'
                },
                {
                    'step': 4,
                    'title': f'Implement improvements ({len(medium_priority)} items)',
                    'description': 'Apply medium-priority recommendations',
                    'items': [r['title'] for r in medium_priority[:5]]
                },
                {
                    'step': 5,
                    'title': 'Run tests',
                    'description': 'Verify all tests pass after changes',
                    'command': 'pytest / npm test / go test / cargo test'
                },
                {
                    'step': 6,
                    'title': f'Polish and optimize ({len(low_priority)} items)',
                    'description': 'Apply low-priority improvements',
                    'items': [r['title'] for r in low_priority[:3]]
                },
                {
                    'step': 7,
                    'title': 'Review and commit',
                    'description': 'Review changes and create commits',
                    'command': 'git add . && git commit -m "Modernize codebase"'
                },
                {
                    'step': 8,
                    'title': 'Create pull request',
                    'description': 'Push changes and create PR for review',
                    'command': 'git push origin modernize-repo'
                }
            ]
        }


def analyze_repo_and_recommend_tool(workspace_dir: str, max_files: int = 50, focus_paths: Optional[List[str]] = None) -> Dict[str, Any]:
    """Tool wrapper for repository analysis.
    
    Args:
        workspace_dir: Root directory of the repository
        max_files: Maximum number of files to analyze (default: 50)
        focus_paths: Optional list of specific paths to focus on
        
    Returns:
        Analysis results with recommendations and migration plan
    """
    analyzer = RepoAnalyzer(workspace_dir)
    return analyzer.analyze_repository(max_files=max_files, focus_paths=focus_paths)
