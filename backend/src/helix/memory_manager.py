"""Persistent memory manager for Helix AI agent.

Stores conversation history, project context, and agent facts to maintain
continuity across sessions. Implements rotation and TTL policies.
"""
from typing import Dict, List, Any, Optional
import json
import os
from pathlib import Path
from datetime import datetime, timedelta


class MemoryManager:
    """Manages persistent memory storage for the AI agent."""
    
    def __init__(self, workspace_dir: str, memory_file: str = ".helix/memory.json"):
        """Initialize the memory manager.
        
        Args:
            workspace_dir: Root directory of the workspace
            memory_file: Relative path to memory file (default: .helix/memory.json)
        """
        self.workspace_dir = Path(workspace_dir)
        self.memory_file = self.workspace_dir / memory_file
        self._ensure_memory_dir()
        
        # Configuration
        self.max_messages = 1000  # Maximum conversation messages
        self.max_facts = 500  # Maximum stored facts
        self.ttl_days = 30  # Time-to-live for old entries
        
        # Load existing memory
        self.memory = self._load_memory()
    
    def _ensure_memory_dir(self):
        """Ensure .helix directory exists."""
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _load_memory(self) -> Dict[str, Any]:
        """Load memory from disk.
        
        Returns:
            Memory dictionary with conversation, facts, and metadata
        """
        if not self.memory_file.exists():
            return self._create_empty_memory()
        
        try:
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                memory = json.load(f)
            
            # Validate structure
            required_keys = ['conversation', 'facts', 'project_context', 'metadata']
            if not all(key in memory for key in required_keys):
                print("⚠️ Memory file corrupted, creating new one")
                return self._create_empty_memory()
            
            return memory
        
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️ Failed to load memory: {str(e)}")
            return self._create_empty_memory()
    
    def _create_empty_memory(self) -> Dict[str, Any]:
        """Create empty memory structure.
        
        Returns:
            Empty memory dictionary
        """
        return {
            'conversation': [],
            'facts': [],
            'project_context': {
                'languages': [],
                'frameworks': [],
                'key_files': [],
                'description': ''
            },
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'version': '1.0'
            }
        }
    
    def _save_memory(self) -> bool:
        """Save memory to disk.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update metadata
            self.memory['metadata']['last_updated'] = datetime.now().isoformat()
            
            # Write to disk
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.memory, f, indent=2, ensure_ascii=False)
            
            # Set restrictive permissions
            os.chmod(self.memory_file, 0o600)
            
            return True
        
        except Exception as e:
            print(f"❌ Failed to save memory: {str(e)}")
            return False
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None) -> bool:
        """Add a message to conversation history.
        
        Args:
            role: Message role ('user' or 'assistant')
            content: Message content
            metadata: Optional metadata (agent name, timestamp, etc.)
            
        Returns:
            True if successful
        """
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }
        
        if metadata:
            message['metadata'] = metadata
        
        self.memory['conversation'].append(message)
        
        # Apply rotation if needed
        if len(self.memory['conversation']) > self.max_messages:
            self._rotate_messages()
        
        return self._save_memory()
    
    def add_fact(self, category: str, key: str, value: Any, ttl_days: Optional[int] = None) -> bool:
        """Add a fact to memory.
        
        Args:
            category: Fact category (e.g., 'project', 'user_preference', 'code_pattern')
            key: Fact key
            value: Fact value
            ttl_days: Optional time-to-live in days (overrides default)
            
        Returns:
            True if successful
        """
        ttl = ttl_days if ttl_days is not None else self.ttl_days
        expires_at = (datetime.now() + timedelta(days=ttl)).isoformat()
        
        fact = {
            'category': category,
            'key': key,
            'value': value,
            'created_at': datetime.now().isoformat(),
            'expires_at': expires_at
        }
        
        # Remove existing fact with same category/key
        self.memory['facts'] = [
            f for f in self.memory['facts']
            if not (f['category'] == category and f['key'] == key)
        ]
        
        self.memory['facts'].append(fact)
        
        # Apply rotation if needed
        if len(self.memory['facts']) > self.max_facts:
            self._rotate_facts()
        
        return self._save_memory()
    
    def get_fact(self, category: str, key: str) -> Optional[Any]:
        """Retrieve a fact from memory.
        
        Args:
            category: Fact category
            key: Fact key
            
        Returns:
            Fact value if found and not expired, None otherwise
        """
        for fact in self.memory['facts']:
            if fact['category'] == category and fact['key'] == key:
                # Check if expired
                expires_at = datetime.fromisoformat(fact['expires_at'])
                if expires_at > datetime.now():
                    return fact['value']
                else:
                    # Remove expired fact
                    self.memory['facts'].remove(fact)
                    self._save_memory()
                    return None
        
        return None
    
    def get_conversation_history(self, limit: Optional[int] = None, since: Optional[datetime] = None) -> List[Dict]:
        """Get conversation history.
        
        Args:
            limit: Maximum number of messages to return (most recent)
            since: Only return messages after this timestamp
            
        Returns:
            List of conversation messages
        """
        messages = self.memory['conversation']
        
        if since:
            messages = [
                msg for msg in messages
                if datetime.fromisoformat(msg['timestamp']) > since
            ]
        
        if limit:
            messages = messages[-limit:]
        
        return messages
    
    def update_project_context(self, **kwargs) -> bool:
        """Update project context.
        
        Args:
            **kwargs: Context fields to update (languages, frameworks, key_files, description)
            
        Returns:
            True if successful
        """
        for key, value in kwargs.items():
            if key in self.memory['project_context']:
                self.memory['project_context'][key] = value
        
        return self._save_memory()
    
    def get_project_context(self) -> Dict[str, Any]:
        """Get project context.
        
        Returns:
            Project context dictionary
        """
        return self.memory['project_context'].copy()
    
    def search_facts(self, category: Optional[str] = None, query: Optional[str] = None) -> List[Dict]:
        """Search facts by category or query string.
        
        Args:
            category: Filter by category
            query: Search in keys and string values
            
        Returns:
            List of matching facts
        """
        facts = self.memory['facts']
        
        # Remove expired facts
        now = datetime.now()
        facts = [
            f for f in facts
            if datetime.fromisoformat(f['expires_at']) > now
        ]
        
        if category:
            facts = [f for f in facts if f['category'] == category]
        
        if query:
            query_lower = query.lower()
            facts = [
                f for f in facts
                if query_lower in f['key'].lower() or
                   (isinstance(f['value'], str) and query_lower in f['value'].lower())
            ]
        
        return facts
    
    def _rotate_messages(self):
        """Rotate old conversation messages."""
        # Keep most recent messages
        self.memory['conversation'] = self.memory['conversation'][-self.max_messages:]
        print(f"🔄 Rotated conversation history to {self.max_messages} messages")
    
    def _rotate_facts(self):
        """Rotate old facts, prioritizing non-expired ones."""
        # Remove expired facts first
        now = datetime.now()
        valid_facts = [
            f for f in self.memory['facts']
            if datetime.fromisoformat(f['expires_at']) > now
        ]
        
        # Keep most recent valid facts
        if len(valid_facts) > self.max_facts:
            valid_facts = sorted(
                valid_facts,
                key=lambda f: datetime.fromisoformat(f['created_at']),
                reverse=True
            )[:self.max_facts]
        
        self.memory['facts'] = valid_facts
        print(f"🔄 Rotated facts to {len(valid_facts)} items")
    
    def clear_conversation(self) -> bool:
        """Clear conversation history.
        
        Returns:
            True if successful
        """
        self.memory['conversation'] = []
        return self._save_memory()
    
    def clear_facts(self, category: Optional[str] = None) -> bool:
        """Clear facts (optionally filtered by category).
        
        Args:
            category: If provided, only clear facts in this category
            
        Returns:
            True if successful
        """
        if category:
            self.memory['facts'] = [
                f for f in self.memory['facts']
                if f['category'] != category
            ]
        else:
            self.memory['facts'] = []
        
        return self._save_memory()
    
    def export_memory(self, export_path: Optional[str] = None) -> Dict[str, Any]:
        """Export memory to a file or return as dictionary.
        
        Args:
            export_path: Optional path to export to (if None, returns dictionary)
            
        Returns:
            Exported memory dictionary
        """
        export_data = self.memory.copy()
        
        if export_path:
            try:
                with open(export_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                print(f"✅ Memory exported to {export_path}")
            except Exception as e:
                print(f"❌ Failed to export memory: {str(e)}")
        
        return export_data
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics.
        
        Returns:
            Dictionary with memory stats
        """
        now = datetime.now()
        valid_facts = [
            f for f in self.memory['facts']
            if datetime.fromisoformat(f['expires_at']) > now
        ]
        
        return {
            'conversation_messages': len(self.memory['conversation']),
            'total_facts': len(self.memory['facts']),
            'valid_facts': len(valid_facts),
            'expired_facts': len(self.memory['facts']) - len(valid_facts),
            'created_at': self.memory['metadata']['created_at'],
            'last_updated': self.memory['metadata']['last_updated'],
            'memory_file': str(self.memory_file),
            'file_size_kb': round(self.memory_file.stat().st_size / 1024, 2) if self.memory_file.exists() else 0
        }
