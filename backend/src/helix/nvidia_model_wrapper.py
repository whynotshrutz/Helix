"""Custom NVIDIA model wrapper to handle empty message filtering.

This wrapper prevents the 'string_too_short' error by filtering out
empty messages before they reach the NVIDIA API.
"""
from typing import List, Dict, Any, Optional

try:
    from phi.models.nvidia import Nvidia
except ImportError:
    from agno.models.nvidia import Nvidia


class NvidiaModelWrapper(Nvidia):
    """Wrapper around Nvidia model that filters empty messages."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def _filter_empty_messages(self, messages: List[Any]) -> List[Any]:
        """Filter out messages with empty content.
        
        Args:
            messages: List of message objects or dictionaries
            
        Returns:
            Filtered list with no empty content messages
        """
        filtered = []
        for msg in messages:
            # Handle both dict and Message object
            if isinstance(msg, dict):
                content = msg.get('content', '')
                role = msg.get('role', 'unknown')
            else:
                # Message object - use attributes
                content = getattr(msg, 'content', '')
                role = getattr(msg, 'role', 'unknown')
            
            # Skip if content is empty string
            if isinstance(content, str) and content.strip() == '':
                print(f"⚠️  Filtered empty message: {role} role")
                continue
            
            # Skip if content is None
            if content is None:
                print(f"⚠️  Filtered None content: {role} role")
                continue
            
            filtered.append(msg)
        
        return filtered
    
    def invoke(self, messages: List[Any], **kwargs) -> Any:
        """Override invoke to filter messages first."""
        filtered_messages = self._filter_empty_messages(messages)
        
        if not filtered_messages:
            print("⚠️  All messages filtered! Using original messages to avoid empty list.")
            filtered_messages = messages
        
        return super().invoke(filtered_messages, **kwargs)
    
    async def ainvoke(self, messages: List[Any], **kwargs) -> Any:
        """Override async invoke to filter messages first."""
        filtered_messages = self._filter_empty_messages(messages)
        
        if not filtered_messages:
            print("⚠️  All messages filtered! Using original messages to avoid empty list.")
            filtered_messages = messages
        
        return await super().ainvoke(filtered_messages, **kwargs)
