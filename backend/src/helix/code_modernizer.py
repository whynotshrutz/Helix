"""Code Modernization and Recommendation System.

Analyzes legacy/old code and provides modernization recommendations
based on latest best practices, documentation, and web research.
"""
from typing import Dict, Any, List, Optional
import os
from pathlib import Path
import re
from datetime import datetime


class CodeModernizer:
    """Analyzes old code and provides modernization recommendations."""
    
    def __init__(self, web_search_manager, semantic_analyzer):
        """Initialize code modernizer.
        
        Args:
            web_search_manager: WebSearchManager instance for research
            semantic_analyzer: SemanticAnalyzer for code analysis
        """
        self.web_search = web_search_manager
        self.semantic = semantic_analyzer
        self.supported_languages = {
            'python': ['.py'],
            'javascript': ['.js', '.jsx'],
            'typescript': ['.ts', '.tsx'],
            'java': ['.java'],
            'go': ['.go'],
            'rust': ['.rs'],
            'cpp': ['.cpp', '.cc', '.cxx'],
            'c': ['.c', '.h'],
        }
    
    def analyze_and_recommend(
        self,
        code: str,
        file_path: Optional[str] = None,
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Analyze code and provide modernization recommendations.
        
        Args:
            code: Source code to analyze
            file_path: Optional file path (helps detect language)
            language: Optional language override
            
        Returns:
            Analysis results with recommendations
        """
        # Detect language
        if not language:
            language = self._detect_language(code, file_path)
        
        print(f"\n{'='*60}")
        print(f"🔍 CODE MODERNIZATION ANALYSIS")
        print(f"{'='*60}\n")
        print(f"📝 Language: {language}")
        if file_path:
            print(f"📁 File: {file_path}")
        print()
        
        # Step 1: Analyze the old code
        print("🔬 Analyzing code structure and patterns...")
        analysis = self._analyze_code_structure(code, language)
        
        # Step 2: Detect outdated patterns
        print("🕰️  Detecting outdated patterns...")
        outdated_patterns = self._detect_outdated_patterns(code, language, analysis)
        
        # Step 3: Search for latest best practices
        print("🌐 Researching latest best practices...")
        best_practices = self._research_best_practices(language, outdated_patterns)
        
        # Step 4: Search for modern alternatives
        print("🔍 Finding modern alternatives...")
        modern_alternatives = self._find_modern_alternatives(
            language, outdated_patterns, analysis
        )
        
        # Step 5: Generate recommendations
        print("💡 Generating recommendations...")
        recommendations = self._generate_recommendations(
            code,
            language,
            analysis,
            outdated_patterns,
            best_practices,
            modern_alternatives,
        )
        
        # Step 6: Create migration guide
        print("📖 Creating migration guide...")
        migration_guide = self._create_migration_guide(
            language, recommendations
        )
        
        result = {
            "ok": True,
            "language": language,
            "file_path": file_path,
            "analysis": analysis,
            "outdated_patterns": outdated_patterns,
            "best_practices": best_practices,
            "modern_alternatives": modern_alternatives,
            "recommendations": recommendations,
            "migration_guide": migration_guide,
            "timestamp": datetime.now().isoformat(),
        }
        
        print(f"\n{'='*60}")
        print(f"✅ Analysis Complete")
        print(f"{'='*60}\n")
        
        return result
    
    def _detect_language(self, code: str, file_path: Optional[str]) -> str:
        """Detect programming language."""
        if file_path:
            ext = Path(file_path).suffix.lower()
            for lang, extensions in self.supported_languages.items():
                if ext in extensions:
                    return lang
        
        # Fallback: detect from code patterns
        if 'def ' in code and 'import ' in code:
            return 'python'
        elif 'function' in code and ('const ' in code or 'let ' in code):
            return 'javascript'
        elif 'public class' in code or 'private ' in code:
            return 'java'
        
        return 'unknown'
    
    def _analyze_code_structure(self, code: str, language: str) -> Dict[str, Any]:
        """Analyze code structure and components."""
        analysis = {
            "lines_of_code": len(code.split('\n')),
            "imports": [],
            "functions": [],
            "classes": [],
            "dependencies": [],
            "patterns": [],
        }
        
        if language == 'python':
            # Extract imports
            import_pattern = r'^(?:from\s+(\S+)\s+)?import\s+(.+)$'
            for match in re.finditer(import_pattern, code, re.MULTILINE):
                analysis['imports'].append(match.group(0))
            
            # Extract functions
            func_pattern = r'^def\s+(\w+)\s*\('
            for match in re.finditer(func_pattern, code, re.MULTILINE):
                analysis['functions'].append(match.group(1))
            
            # Extract classes
            class_pattern = r'^class\s+(\w+)'
            for match in re.finditer(class_pattern, code, re.MULTILINE):
                analysis['classes'].append(match.group(1))
        
        elif language == 'javascript' or language == 'typescript':
            # Extract imports
            import_pattern = r'(?:import|require)\s*\(?[\'"](.+?)[\'"]'
            for match in re.finditer(import_pattern, code):
                analysis['imports'].append(match.group(1))
            
            # Extract functions
            func_pattern = r'(?:function|const|let|var)\s+(\w+)\s*=?\s*(?:\([^)]*\)|async)?'
            for match in re.finditer(func_pattern, code):
                analysis['functions'].append(match.group(1))
        
        return analysis
    
    def _detect_outdated_patterns(
        self, code: str, language: str, analysis: Dict
    ) -> List[Dict[str, Any]]:
        """Detect outdated patterns in code."""
        outdated = []
        
        if language == 'python':
            # Check Python version indicators
            if 'print ' in code and 'print(' not in code:
                outdated.append({
                    "pattern": "Python 2 print statements",
                    "severity": "high",
                    "description": "Using Python 2 print statements instead of Python 3 print()",
                })
            
            # Check for old string formatting
            if '%s' in code or '%d' in code:
                outdated.append({
                    "pattern": "Old string formatting (% operator)",
                    "severity": "medium",
                    "description": "Using old % string formatting instead of f-strings or .format()",
                })
            
            # Check for deprecated modules
            deprecated_modules = ['imp', 'optparse', 'asyncore']
            for module in deprecated_modules:
                if f'import {module}' in code:
                    outdated.append({
                        "pattern": f"Deprecated module: {module}",
                        "severity": "high",
                        "description": f"Module '{module}' is deprecated",
                    })
            
            # Check for old exception syntax
            if re.search(r'except\s+\w+\s*,\s*\w+:', code):
                outdated.append({
                    "pattern": "Old exception syntax",
                    "severity": "high",
                    "description": "Using Python 2 exception syntax (except Exception, e:)",
                })
            
            # Check for missing type hints (Python 3.5+)
            if 'def ' in code and '->' not in code and ':' not in code.split('def')[1].split('\n')[0]:
                outdated.append({
                    "pattern": "Missing type hints",
                    "severity": "low",
                    "description": "Functions lack type hints (modern Python best practice)",
                })
        
        elif language == 'javascript':
            # Check for var usage
            if re.search(r'\bvar\b', code):
                outdated.append({
                    "pattern": "Using 'var' instead of 'let'/'const'",
                    "severity": "medium",
                    "description": "var has function scope issues, use let/const",
                })
            
            # Check for callback hell
            if code.count('function(') > 3 and 'async' not in code:
                outdated.append({
                    "pattern": "Callback hell",
                    "severity": "high",
                    "description": "Multiple nested callbacks, should use async/await",
                })
            
            # Check for jQuery
            if '$(' in code or 'jQuery' in code:
                outdated.append({
                    "pattern": "jQuery dependency",
                    "severity": "medium",
                    "description": "Modern JS has native alternatives to jQuery",
                })
        
        return outdated
    
    def _research_best_practices(
        self, language: str, outdated_patterns: List[Dict]
    ) -> Dict[str, Any]:
        """Research latest best practices from the web."""
        if not self.web_search:
            return {"ok": False, "error": "Web search not available"}
        
        # Search for general best practices
        query = f"{language} best practices 2024 2025 modern coding standards"
        general_results = self.web_search.search_best_practices(
            technology=language,
            area="modern development",
            max_results=3,
        )
        
        # Search for specific pattern alternatives
        pattern_results = []
        for pattern in outdated_patterns[:3]:  # Limit to top 3 patterns
            pattern_query = f"{language} modern alternative to {pattern['pattern']} latest"
            result = self.web_search.search(
                query=pattern_query,
                provider="auto",
                max_results=2,
                search_type="docs",
            )
            if result.get("ok"):
                pattern_results.append({
                    "pattern": pattern['pattern'],
                    "results": result,
                })
        
        return {
            "ok": True,
            "general_best_practices": general_results,
            "pattern_alternatives": pattern_results,
        }
    
    def _find_modern_alternatives(
        self, language: str, outdated_patterns: List[Dict], analysis: Dict
    ) -> List[Dict[str, Any]]:
        """Find modern alternatives for outdated patterns."""
        alternatives = []
        
        if language == 'python':
            for pattern in outdated_patterns:
                if 'print statements' in pattern['pattern']:
                    alternatives.append({
                        "pattern": pattern['pattern'],
                        "modern_alternative": "print() function",
                        "example": "print('Hello, World!')",
                        "reason": "Python 3 standard, consistent with other functions",
                    })
                
                elif 'string formatting' in pattern['pattern']:
                    alternatives.append({
                        "pattern": pattern['pattern'],
                        "modern_alternative": "f-strings (Python 3.6+)",
                        "example": "f'Hello, {name}!'",
                        "reason": "Faster, more readable, less error-prone",
                    })
                
                elif 'type hints' in pattern['pattern']:
                    alternatives.append({
                        "pattern": pattern['pattern'],
                        "modern_alternative": "Type annotations (PEP 484)",
                        "example": "def func(x: int) -> str:\n    return str(x)",
                        "reason": "Better IDE support, catches bugs early, self-documenting",
                    })
        
        elif language == 'javascript':
            for pattern in outdated_patterns:
                if 'var' in pattern['pattern']:
                    alternatives.append({
                        "pattern": pattern['pattern'],
                        "modern_alternative": "let/const (ES6+)",
                        "example": "const name = 'John';\nlet age = 30;",
                        "reason": "Block scope, prevents hoisting issues",
                    })
                
                elif 'callback' in pattern['pattern'].lower():
                    alternatives.append({
                        "pattern": pattern['pattern'],
                        "modern_alternative": "async/await (ES2017+)",
                        "example": "async function getData() {\n  const result = await fetch(url);\n  return result;\n}",
                        "reason": "More readable, easier error handling, synchronous-looking async code",
                    })
        
        return alternatives
    
    def _generate_recommendations(
        self,
        code: str,
        language: str,
        analysis: Dict,
        outdated_patterns: List[Dict],
        best_practices: Dict,
        modern_alternatives: List[Dict],
    ) -> List[Dict[str, Any]]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Priority 1: Critical outdated patterns
        for pattern in outdated_patterns:
            if pattern['severity'] == 'high':
                alt = next((a for a in modern_alternatives if a['pattern'] == pattern['pattern']), None)
                recommendations.append({
                    "priority": "high",
                    "category": "modernization",
                    "title": f"Update {pattern['pattern']}",
                    "description": pattern['description'],
                    "alternative": alt['modern_alternative'] if alt else "See documentation",
                    "example": alt['example'] if alt else None,
                    "reason": alt['reason'] if alt else None,
                })
        
        # Priority 2: Medium severity patterns
        for pattern in outdated_patterns:
            if pattern['severity'] == 'medium':
                alt = next((a for a in modern_alternatives if a['pattern'] == pattern['pattern']), None)
                recommendations.append({
                    "priority": "medium",
                    "category": "improvement",
                    "title": f"Consider updating {pattern['pattern']}",
                    "description": pattern['description'],
                    "alternative": alt['modern_alternative'] if alt else "See documentation",
                    "example": alt['example'] if alt else None,
                    "reason": alt['reason'] if alt else None,
                })
        
        # Priority 3: General improvements
        recommendations.append({
            "priority": "low",
            "category": "best_practice",
            "title": "Follow modern best practices",
            "description": f"Review latest {language} best practices",
            "web_resources": best_practices.get('general_best_practices', {}),
        })
        
        return recommendations
    
    def _create_migration_guide(
        self, language: str, recommendations: List[Dict]
    ) -> Dict[str, Any]:
        """Create step-by-step migration guide."""
        guide = {
            "title": f"Code Modernization Guide for {language.title()}",
            "steps": [],
            "estimated_time": "2-4 hours",
            "difficulty": "medium",
        }
        
        # Step 1: Backup
        guide['steps'].append({
            "step": 1,
            "title": "Backup your code",
            "description": "Create a git branch or backup before making changes",
            "commands": [
                "git checkout -b modernize-code",
                "git add .",
                "git commit -m 'Backup before modernization'",
            ],
        })
        
        # Step 2: Update dependencies
        guide['steps'].append({
            "step": 2,
            "title": "Update dependencies",
            "description": "Update to latest stable versions",
            "commands": [
                "pip install --upgrade pip" if language == 'python' else "npm update",
            ],
        })
        
        # Step 3: Apply high-priority changes
        high_priority = [r for r in recommendations if r['priority'] == 'high']
        if high_priority:
            guide['steps'].append({
                "step": 3,
                "title": "Fix critical issues",
                "description": "Address high-priority modernization needs",
                "changes": high_priority,
            })
        
        # Step 4: Apply medium-priority changes
        medium_priority = [r for r in recommendations if r['priority'] == 'medium']
        if medium_priority:
            guide['steps'].append({
                "step": 4,
                "title": "Implement improvements",
                "description": "Apply recommended improvements",
                "changes": medium_priority,
            })
        
        # Step 5: Test
        guide['steps'].append({
            "step": 5,
            "title": "Test thoroughly",
            "description": "Run tests and verify functionality",
            "commands": [
                "pytest" if language == 'python' else "npm test",
            ],
        })
        
        # Step 6: Review and commit
        guide['steps'].append({
            "step": 6,
            "title": "Review and commit",
            "description": "Review all changes and commit",
            "commands": [
                "git diff",
                "git add .",
                "git commit -m 'Modernize code'",
            ],
        })
        
        return guide
