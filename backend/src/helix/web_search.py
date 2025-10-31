"""Web Search Integration for Helix - Tavily and Exa support.

This module integrates real-time web search capabilities using Tavily and Exa APIs
for documentation retrieval and knowledge enhancement.
"""
from typing import List, Dict, Any, Optional, Literal
import os
from datetime import datetime
import json
from pathlib import Path

try:
    from agno.tools.tavily import TavilyTools
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False
    print("Warning: Tavily not available. Install with: pip install agno[tavily]")

try:
    from agno.tools.exa import ExaTools
    EXA_AVAILABLE = True
except ImportError:
    EXA_AVAILABLE = False
    print("Warning: Exa not available. Install with: pip install agno[exa]")


class WebSearchManager:
    """Manages web search operations using Tavily and Exa."""
    
    def __init__(
        self,
        tavily_api_key: Optional[str] = None,
        exa_api_key: Optional[str] = None,
        cache_dir: str = "./tmp/search_cache",
        cache_ttl: int = 86400,  # 24 hours
    ):
        """Initialize web search manager.
        
        Args:
            tavily_api_key: Tavily API key (or from TAVILY_API_KEY env)
            exa_api_key: Exa API key (or from EXA_API_KEY env)
            cache_dir: Directory to cache search results
            cache_ttl: Cache time-to-live in seconds
        """
        self.tavily_api_key = tavily_api_key or os.getenv("TAVILY_API_KEY")
        self.exa_api_key = exa_api_key or os.getenv("EXA_API_KEY")
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl = cache_ttl
        
        # Initialize tools if available
        self.tavily_tools = None
        self.exa_tools = None
        
        if TAVILY_AVAILABLE and self.tavily_api_key:
            try:
                self.tavily_tools = TavilyTools(api_key=self.tavily_api_key)
                print("✓ Tavily search enabled")
            except Exception as e:
                print(f"Warning: Failed to initialize Tavily: {e}")
        
        if EXA_AVAILABLE and self.exa_api_key:
            try:
                self.exa_tools = ExaTools(api_key=self.exa_api_key)
                print("✓ Exa search enabled")
            except Exception as e:
                print(f"Warning: Failed to initialize Exa: {e}")
    
    def search(
        self,
        query: str,
        provider: Literal["tavily", "exa", "auto"] = "auto",
        max_results: int = 5,
        search_type: str = "general",
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """Search the web for documentation and information.
        
        Args:
            query: Search query
            provider: Which provider to use (tavily, exa, or auto)
            max_results: Maximum number of results
            search_type: Type of search (general, docs, code, etc.)
            use_cache: Whether to use cached results
            
        Returns:
            Search results dict
        """
        # Check cache first
        if use_cache:
            cached = self._get_from_cache(query, provider)
            if cached:
                return cached
        
        # Determine provider
        if provider == "auto":
            # Use Tavily for general search, Exa for technical docs
            if search_type in ["docs", "code", "technical"]:
                provider = "exa" if self.exa_tools else "tavily"
            else:
                provider = "tavily" if self.tavily_tools else "exa"
        
        # Perform search
        results = None
        if provider == "tavily" and self.tavily_tools:
            results = self._search_tavily(query, max_results, search_type)
        elif provider == "exa" and self.exa_tools:
            results = self._search_exa(query, max_results, search_type)
        else:
            return {
                "ok": False,
                "error": f"Provider '{provider}' not available",
                "message": "Configure API keys: TAVILY_API_KEY or EXA_API_KEY",
            }
        
        # Cache results
        if results and results.get("ok") and use_cache:
            self._save_to_cache(query, provider, results)
        
        return results
    
    def search_documentation(
        self,
        technology: str,
        topic: str,
        max_results: int = 3,
    ) -> Dict[str, Any]:
        """Search for technical documentation.
        
        Args:
            technology: Technology name (e.g., "FastAPI", "React", "Python")
            topic: Specific topic (e.g., "async endpoints", "hooks", "decorators")
            max_results: Maximum results
            
        Returns:
            Documentation search results
        """
        query = f"{technology} {topic} documentation latest"
        return self.search(
            query=query,
            provider="auto",
            max_results=max_results,
            search_type="docs",
        )
    
    def search_error_solution(
        self,
        error_message: str,
        context: Optional[str] = None,
        max_results: int = 3,
    ) -> Dict[str, Any]:
        """Search for solutions to an error.
        
        Args:
            error_message: Error message or exception
            context: Optional context (language, framework)
            max_results: Maximum results
            
        Returns:
            Solution search results
        """
        query = f"{error_message}"
        if context:
            query = f"{context} {query}"
        query += " solution fix stackoverflow"
        
        return self.search(
            query=query,
            provider="tavily",  # Tavily better for error solutions
            max_results=max_results,
            search_type="general",
        )
    
    def search_best_practices(
        self,
        technology: str,
        area: str,
        max_results: int = 3,
    ) -> Dict[str, Any]:
        """Search for best practices.
        
        Args:
            technology: Technology name
            area: Area of interest (e.g., "security", "performance", "testing")
            max_results: Maximum results
            
        Returns:
            Best practices search results
        """
        query = f"{technology} {area} best practices 2024"
        return self.search(
            query=query,
            provider="auto",
            max_results=max_results,
            search_type="docs",
        )
    
    def _search_tavily(
        self,
        query: str,
        max_results: int,
        search_type: str,
    ) -> Dict[str, Any]:
        """Search using Tavily.
        
        Args:
            query: Search query
            max_results: Maximum results
            search_type: Search type
            
        Returns:
            Tavily search results
        """
        if not self.tavily_tools:
            return {"ok": False, "error": "tavily_not_available"}
        
        try:
            # Tavily search options
            search_depth = "advanced" if search_type in ["docs", "technical"] else "basic"
            
            # Call Tavily search
            # Note: Actual Tavily API call may differ based on agno.tools.tavily implementation
            results = self.tavily_tools.search(
                query=query,
                max_results=max_results,
                search_depth=search_depth,
                include_answer=True,
                include_raw_content=False,
            )
            
            # Format results
            formatted_results = self._format_tavily_results(results)
            
            return {
                "ok": True,
                "provider": "tavily",
                "query": query,
                "results": formatted_results,
                "timestamp": datetime.now().isoformat(),
            }
        
        except Exception as e:
            return {
                "ok": False,
                "error": "tavily_search_failed",
                "message": str(e),
            }
    
    def _search_exa(
        self,
        query: str,
        max_results: int,
        search_type: str,
    ) -> Dict[str, Any]:
        """Search using Exa.
        
        Args:
            query: Search query
            max_results: Maximum results
            search_type: Search type
            
        Returns:
            Exa search results
        """
        if not self.exa_tools:
            return {"ok": False, "error": "exa_not_available"}
        
        try:
            # Exa is optimized for technical content
            # Note: Actual Exa API call may differ based on agno.tools.exa implementation
            results = self.exa_tools.search(
                query=query,
                num_results=max_results,
                type="neural",  # Use neural search for better semantic matching
                use_autoprompt=True,  # Let Exa optimize the query
            )
            
            # Format results
            formatted_results = self._format_exa_results(results)
            
            return {
                "ok": True,
                "provider": "exa",
                "query": query,
                "results": formatted_results,
                "timestamp": datetime.now().isoformat(),
            }
        
        except Exception as e:
            return {
                "ok": False,
                "error": "exa_search_failed",
                "message": str(e),
            }
    
    def _format_tavily_results(self, results: Any) -> List[Dict[str, Any]]:
        """Format Tavily results to standard format.
        
        Args:
            results: Raw Tavily results
            
        Returns:
            Formatted results list
        """
        formatted = []
        
        # Handle different result formats
        if isinstance(results, dict) and "results" in results:
            items = results["results"]
        elif isinstance(results, list):
            items = results
        else:
            return formatted
        
        for item in items:
            formatted.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": item.get("content", ""),
                "score": item.get("score", 0.0),
            })
        
        return formatted
    
    def _format_exa_results(self, results: Any) -> List[Dict[str, Any]]:
        """Format Exa results to standard format.
        
        Args:
            results: Raw Exa results
            
        Returns:
            Formatted results list
        """
        formatted = []
        
        # Handle different result formats
        if isinstance(results, dict) and "results" in results:
            items = results["results"]
        elif isinstance(results, list):
            items = results
        else:
            return formatted
        
        for item in items:
            formatted.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": item.get("text", item.get("content", "")),
                "score": item.get("score", 0.0),
            })
        
        return formatted
    
    def _get_cache_key(self, query: str, provider: str) -> str:
        """Generate cache key for query.
        
        Args:
            query: Search query
            provider: Provider name
            
        Returns:
            Cache key
        """
        import hashlib
        key = f"{provider}:{query}"
        return hashlib.md5(key.encode()).hexdigest()
    
    def _get_from_cache(self, query: str, provider: str) -> Optional[Dict[str, Any]]:
        """Get cached search results.
        
        Args:
            query: Search query
            provider: Provider name
            
        Returns:
            Cached results or None
        """
        cache_key = self._get_cache_key(query, provider)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            data = json.loads(cache_file.read_text())
            
            # Check if expired
            cached_time = datetime.fromisoformat(data.get("timestamp", ""))
            age = (datetime.now() - cached_time).total_seconds()
            
            if age > self.cache_ttl:
                cache_file.unlink()  # Delete expired cache
                return None
            
            return data
        
        except Exception as e:
            print(f"Cache read error: {e}")
            return None
    
    def _save_to_cache(self, query: str, provider: str, results: Dict[str, Any]) -> None:
        """Save search results to cache.
        
        Args:
            query: Search query
            provider: Provider name
            results: Results to cache
        """
        cache_key = self._get_cache_key(query, provider)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            cache_file.write_text(json.dumps(results, indent=2))
        except Exception as e:
            print(f"Cache write error: {e}")
    
    def clear_cache(self) -> None:
        """Clear all cached search results."""
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()


# Global search manager instance
_search_manager: Optional[WebSearchManager] = None


def get_search_manager(**kwargs) -> WebSearchManager:
    """Get or create global search manager instance.
    
    Args:
        **kwargs: Arguments to pass to WebSearchManager constructor
        
    Returns:
        WebSearchManager instance
    """
    global _search_manager
    
    if _search_manager is None:
        _search_manager = WebSearchManager(**kwargs)
    
    return _search_manager


# Convenience functions
def search_web(query: str, **kwargs) -> Dict[str, Any]:
    """Quick web search.
    
    Args:
        query: Search query
        **kwargs: Additional arguments for search()
        
    Returns:
        Search results
    """
    manager = get_search_manager()
    return manager.search(query, **kwargs)


def search_docs(technology: str, topic: str, **kwargs) -> Dict[str, Any]:
    """Quick documentation search.
    
    Args:
        technology: Technology name
        topic: Topic to search for
        **kwargs: Additional arguments
        
    Returns:
        Documentation results
    """
    manager = get_search_manager()
    return manager.search_documentation(technology, topic, **kwargs)
