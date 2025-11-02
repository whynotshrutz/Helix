"""Enhanced Semantic Code Analysis for Helix.

This module provides deep code analysis including:
- Dependency graph construction
- Circular dependency detection
- Unused import detection
- Vulnerability scanning
- Code complexity metrics
- Architecture recommendations
"""
import ast
import re
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass
import json


@dataclass
class ImportNode:
    """Represents an import in the codebase."""
    module: str
    file_path: str
    line_number: int
    is_used: bool = False
    is_external: bool = False


@dataclass
class FunctionMetrics:
    """Metrics for a function."""
    name: str
    file_path: str
    line_number: int
    lines_of_code: int
    cyclomatic_complexity: int
    num_parameters: int
    has_docstring: bool
    calls: List[str]  # Functions this function calls


@dataclass
class VulnerabilityFinding:
    """Represents a potential security vulnerability."""
    severity: str  # critical, high, medium, low
    title: str
    description: str
    file_path: str
    line_number: int
    recommendation: str


class SemanticAnalyzer:
    """Advanced semantic code analyzer."""
    
    def __init__(self, base_dir: str = "."):
        """Initialize the semantic analyzer.
        
        Args:
            base_dir: Base directory to analyze
        """
        self.base_dir = Path(base_dir)
        self.imports: Dict[str, List[ImportNode]] = defaultdict(list)
        self.functions: Dict[str, FunctionMetrics] = {}
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self.vulnerabilities: List[VulnerabilityFinding] = []
        self.file_contents: Dict[str, str] = {}
    
    def analyze(self, file_patterns: List[str] = ["**/*.py"]) -> Dict[str, Any]:
        """Run full semantic analysis.
        
        Args:
            file_patterns: Glob patterns for files to analyze
            
        Returns:
            Comprehensive analysis report
        """
        # Collect all files
        files = []
        for pattern in file_patterns:
            files.extend(self.base_dir.glob(pattern))
        
        # Filter out excluded directories
        excluded = {"node_modules", "venv", "__pycache__", "dist", "build", ".git", "tmp"}
        files = [f for f in files if not any(ex in f.parts for ex in excluded)]
        
        # Analyze each file
        for file_path in files:
            try:
                content = file_path.read_text(encoding="utf-8")
                self.file_contents[str(file_path)] = content
                
                if file_path.suffix == ".py":
                    self._analyze_python_file(file_path, content)
                elif file_path.suffix in [".js", ".ts", ".jsx", ".tsx"]:
                    self._analyze_javascript_file(file_path, content)
                
                # Scan for vulnerabilities
                self._scan_vulnerabilities(file_path, content)
            except Exception as e:
                print(f"Error analyzing {file_path}: {e}")
        
        # Build dependency graph
        self._build_dependency_graph()
        
        # Detect circular dependencies
        circular_deps = self._detect_circular_dependencies()
        
        # Find unused imports
        unused_imports = self._find_unused_imports()
        
        # Calculate complexity metrics
        complex_functions = [
            f for f in self.functions.values()
            if f.cyclomatic_complexity > 10 or f.lines_of_code > 50
        ]
        
        # Generate recommendations
        recommendations = self._generate_semantic_recommendations(
            circular_deps,
            unused_imports,
            complex_functions
        )
        
        return {
            "summary": {
                "total_files": len(files),
                "total_imports": sum(len(imps) for imps in self.imports.values()),
                "total_functions": len(self.functions),
                "vulnerabilities_found": len(self.vulnerabilities),
                "circular_dependencies": len(circular_deps),
                "unused_imports": len(unused_imports),
                "complex_functions": len(complex_functions),
            },
            "dependency_graph": {
                file: list(deps) for file, deps in self.dependency_graph.items()
            },
            "circular_dependencies": circular_deps,
            "unused_imports": [
                {"module": imp.module, "file": imp.file_path, "line": imp.line_number}
                for imp in unused_imports[:20]  # Limit to first 20
            ],
            "vulnerabilities": [
                {
                    "severity": v.severity,
                    "title": v.title,
                    "file": v.file_path,
                    "line": v.line_number,
                    "recommendation": v.recommendation,
                }
                for v in self.vulnerabilities[:10]  # Top 10 vulnerabilities
            ],
            "complex_functions": [
                {
                    "name": f.name,
                    "file": f.file_path,
                    "line": f.line_number,
                    "complexity": f.cyclomatic_complexity,
                    "lines": f.lines_of_code,
                }
                for f in complex_functions[:15]  # Top 15 complex functions
            ],
            "recommendations": recommendations,
        }
    
    def _analyze_python_file(self, file_path: Path, content: str) -> None:
        """Analyze a Python file using AST.
        
        Args:
            file_path: Path to Python file
            content: File content
        """
        try:
            tree = ast.parse(content)
            
            # Extract imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imp = ImportNode(
                            module=alias.name,
                            file_path=str(file_path),
                            line_number=node.lineno,
                            is_external=not self._is_local_import(alias.name),
                        )
                        self.imports[str(file_path)].append(imp)
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imp = ImportNode(
                            module=node.module,
                            file_path=str(file_path),
                            line_number=node.lineno,
                            is_external=not self._is_local_import(node.module),
                        )
                        self.imports[str(file_path)].append(imp)
                
                # Extract function metrics
                elif isinstance(node, ast.FunctionDef):
                    metrics = self._analyze_function(node, file_path)
                    self.functions[f"{file_path}:{node.name}"] = metrics
        
        except SyntaxError as e:
            print(f"Syntax error in {file_path}: {e}")
    
    def _analyze_javascript_file(self, file_path: Path, content: str) -> None:
        """Analyze a JavaScript/TypeScript file using regex patterns.
        
        Args:
            file_path: Path to JS/TS file
            content: File content
        """
        # Extract imports using regex (not perfect, but good enough)
        import_patterns = [
            r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]',  # ES6 imports
            r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',  # CommonJS
        ]
        
        for pattern in import_patterns:
            for match in re.finditer(pattern, content):
                module = match.group(1)
                line_number = content[:match.start()].count('\n') + 1
                
                imp = ImportNode(
                    module=module,
                    file_path=str(file_path),
                    line_number=line_number,
                    is_external=not module.startswith('.'),
                )
                self.imports[str(file_path)].append(imp)
    
    def _analyze_function(self, node: ast.FunctionDef, file_path: Path) -> FunctionMetrics:
        """Analyze a Python function node.
        
        Args:
            node: AST function node
            file_path: Path to file
            
        Returns:
            Function metrics
        """
        # Calculate lines of code
        lines = []
        for child in ast.walk(node):
            if hasattr(child, 'lineno'):
                lines.append(child.lineno)
        loc = max(lines) - min(lines) + 1 if lines else 0
        
        # Calculate cyclomatic complexity (simplified)
        complexity = 1  # Base complexity
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        # Check for docstring
        has_docstring = (
            ast.get_docstring(node) is not None
        )
        
        # Extract function calls
        calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    calls.append(child.func.attr)
        
        return FunctionMetrics(
            name=node.name,
            file_path=str(file_path),
            line_number=node.lineno,
            lines_of_code=loc,
            cyclomatic_complexity=complexity,
            num_parameters=len(node.args.args),
            has_docstring=has_docstring,
            calls=calls,
        )
    
    def _is_local_import(self, module: str) -> bool:
        """Check if an import is local to the project.
        
        Args:
            module: Module name
            
        Returns:
            True if local import
        """
        # Check if module starts with project name or relative import
        if module.startswith('.'):
            return True
        
        # Check if file exists in project
        possible_paths = [
            self.base_dir / f"{module.replace('.', '/')}.py",
            self.base_dir / module.replace('.', '/') / "__init__.py",
        ]
        
        return any(p.exists() for p in possible_paths)
    
    def _build_dependency_graph(self) -> None:
        """Build dependency graph between files."""
        for file_path, imports in self.imports.items():
            for imp in imports:
                if not imp.is_external:
                    # Find the actual file for this import
                    target_file = self._resolve_import_to_file(imp.module)
                    if target_file:
                        self.dependency_graph[file_path].add(target_file)
    
    def _resolve_import_to_file(self, module: str) -> Optional[str]:
        """Resolve a module import to an actual file path.
        
        Args:
            module: Module name
            
        Returns:
            File path or None
        """
        possible_paths = [
            self.base_dir / f"{module.replace('.', '/')}.py",
            self.base_dir / module.replace('.', '/') / "__init__.py",
        ]
        
        for path in possible_paths:
            if path.exists():
                return str(path)
        
        return None
    
    def _detect_circular_dependencies(self) -> List[List[str]]:
        """Detect circular dependencies in the codebase.
        
        Returns:
            List of circular dependency chains
        """
        circular = []
        visited = set()
        path = []
        
        def dfs(node: str) -> None:
            if node in path:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                if cycle not in circular:
                    circular.append(cycle)
                return
            
            if node in visited:
                return
            
            visited.add(node)
            path.append(node)
            
            for neighbor in self.dependency_graph.get(node, []):
                dfs(neighbor)
            
            path.pop()
        
        for node in self.dependency_graph:
            dfs(node)
        
        return circular
    
    def _find_unused_imports(self) -> List[ImportNode]:
        """Find imports that are not used in the code.
        
        Returns:
            List of unused imports
        """
        unused = []
        
        for file_path, imports in self.imports.items():
            if file_path not in self.file_contents:
                continue
            
            content = self.file_contents[file_path]
            
            for imp in imports:
                # Simple heuristic: check if module name appears elsewhere in file
                module_name = imp.module.split('.')[-1]
                
                # Count occurrences (exclude the import line itself)
                lines = content.splitlines()
                occurrences = sum(
                    1 for i, line in enumerate(lines)
                    if i + 1 != imp.line_number and module_name in line
                )
                
                if occurrences == 0:
                    unused.append(imp)
        
        return unused
    
    def _scan_vulnerabilities(self, file_path: Path, content: str) -> None:
        """Scan file for security vulnerabilities.
        
        Args:
            file_path: Path to file
            content: File content
        """
        lines = content.splitlines()
        
        # Pattern-based vulnerability detection
        vuln_patterns = [
            {
                "pattern": r'eval\s*\(',
                "severity": "critical",
                "title": "Unsafe eval() usage",
                "description": "eval() can execute arbitrary code",
                "recommendation": "Use ast.literal_eval() or avoid dynamic code execution",
            },
            {
                "pattern": r'exec\s*\(',
                "severity": "critical",
                "title": "Unsafe exec() usage",
                "description": "exec() can execute arbitrary code",
                "recommendation": "Avoid dynamic code execution or use sandboxed environment",
            },
            {
                "pattern": r'pickle\.loads?\s*\(',
                "severity": "high",
                "title": "Unsafe pickle usage",
                "description": "pickle can execute arbitrary code when deserializing",
                "recommendation": "Use json.loads() or validate input before unpickling",
            },
            {
                "pattern": r'shell\s*=\s*True',
                "severity": "high",
                "title": "Command injection risk",
                "description": "shell=True in subprocess can lead to command injection",
                "recommendation": "Use shell=False and pass arguments as a list",
            },
            {
                "pattern": r'password\s*=\s*["\'][^"\']+["\']',
                "severity": "critical",
                "title": "Hardcoded password",
                "description": "Password hardcoded in source code",
                "recommendation": "Use environment variables or secure credential storage",
            },
            {
                "pattern": r'api[_-]?key\s*=\s*["\'][^"\']+["\']',
                "severity": "critical",
                "title": "Hardcoded API key",
                "description": "API key hardcoded in source code",
                "recommendation": "Use environment variables or secure credential storage",
            },
            {
                "pattern": r'\.innerHTML\s*=',
                "severity": "medium",
                "title": "XSS vulnerability risk",
                "description": "Setting innerHTML can lead to XSS attacks",
                "recommendation": "Use textContent or sanitize HTML input",
            },
            {
                "pattern": r'SELECT\s+.*\s+WHERE\s+.*\+',
                "severity": "high",
                "title": "SQL injection risk",
                "description": "String concatenation in SQL query",
                "recommendation": "Use parameterized queries or ORM",
            },
        ]
        
        for i, line in enumerate(lines):
            for vuln in vuln_patterns:
                if re.search(vuln["pattern"], line, re.IGNORECASE):
                    self.vulnerabilities.append(
                        VulnerabilityFinding(
                            severity=vuln["severity"],
                            title=vuln["title"],
                            description=vuln["description"],
                            file_path=str(file_path),
                            line_number=i + 1,
                            recommendation=vuln["recommendation"],
                        )
                    )
    
    def _generate_semantic_recommendations(
        self,
        circular_deps: List[List[str]],
        unused_imports: List[ImportNode],
        complex_functions: List[FunctionMetrics],
    ) -> List[str]:
        """Generate actionable recommendations based on analysis.
        
        Args:
            circular_deps: Circular dependency chains
            unused_imports: List of unused imports
            complex_functions: List of complex functions
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Circular dependencies
        if circular_deps:
            recommendations.append(
                f"🔄 Found {len(circular_deps)} circular dependencies. "
                "Consider refactoring to break these cycles using dependency injection "
                "or moving shared code to a separate module."
            )
        
        # Unused imports
        if len(unused_imports) > 10:
            recommendations.append(
                f"🧹 Found {len(unused_imports)} unused imports. "
                "Run a linter (pylint, flake8) to automatically remove them."
            )
        
        # Complex functions
        if complex_functions:
            recommendations.append(
                f"📊 Found {len(complex_functions)} complex functions. "
                "Consider breaking down functions with high cyclomatic complexity (>10) "
                "into smaller, more testable units."
            )
        
        # Vulnerabilities
        critical_vulns = [v for v in self.vulnerabilities if v.severity == "critical"]
        if critical_vulns:
            recommendations.append(
                f"🚨 Found {len(critical_vulns)} CRITICAL security issues. "
                "Address these immediately before deploying to production."
            )
        
        # Missing docstrings
        missing_docs = [f for f in self.functions.values() if not f.has_docstring]
        if len(missing_docs) > len(self.functions) * 0.5:
            recommendations.append(
                f"📝 {len(missing_docs)} functions lack docstrings. "
                "Add documentation to improve code maintainability."
            )
        
        # Dependency structure
        if len(self.dependency_graph) > 20:
            avg_deps = sum(len(deps) for deps in self.dependency_graph.values()) / len(self.dependency_graph)
            if avg_deps > 5:
                recommendations.append(
                    f"🏗️ High coupling detected (avg {avg_deps:.1f} dependencies per file). "
                    "Consider applying SOLID principles to reduce coupling."
                )
        
        return recommendations


# Convenience function
def analyze_codebase_semantics(base_dir: str = ".", file_patterns: List[str] = ["**/*.py"]) -> Dict[str, Any]:
    """Run full semantic analysis on codebase.
    
    Args:
        base_dir: Base directory to analyze
        file_patterns: File patterns to include
        
    Returns:
        Analysis report
    """
    analyzer = SemanticAnalyzer(base_dir=base_dir)
    return analyzer.analyze(file_patterns=file_patterns)
