"""User confirmation system for code recommendations and changes.

This module provides a mechanism to ask users for confirmation before
applying recommended changes to their codebase.
"""
from typing import Dict, Any, List, Optional
import json


class RecommendationConfirmation:
    """Manages user confirmations for code recommendations."""
    
    def __init__(self):
        self.pending_recommendations: Dict[str, Dict[str, Any]] = {}
        self.confirmation_id = 0
    
    def create_confirmation_request(
        self,
        title: str,
        description: str,
        changes: List[Dict[str, Any]],
        priority: str = "medium"
    ) -> Dict[str, Any]:
        """Create a confirmation request for recommendations.
        
        Args:
            title: Title of the recommendation
            description: Detailed description
            changes: List of proposed changes
            priority: Priority level (low, medium, high)
            
        Returns:
            Confirmation request dict with unique ID
        """
        self.confirmation_id += 1
        request_id = f"confirm_{self.confirmation_id}"
        
        request = {
            "id": request_id,
            "title": title,
            "description": description,
            "changes": changes,
            "priority": priority,
            "status": "pending"
        }
        
        self.pending_recommendations[request_id] = request
        return request
    
    def format_for_user(self, request: Dict[str, Any]) -> str:
        """Format confirmation request for user display.
        
        Args:
            request: Confirmation request dict
            
        Returns:
            Formatted string for user prompt
        """
        output = []
        output.append(f"🔔 RECOMMENDATION: {request['title']}")
        output.append("=" * 60)
        output.append(f"\n{request['description']}\n")
        
        if request.get('changes'):
            output.append(f"📋 Proposed Changes ({len(request['changes'])}):")
            for i, change in enumerate(request['changes'], 1):
                output.append(f"\n{i}. {change.get('file', 'Unknown file')}")
                output.append(f"   Type: {change.get('type', 'modification')}")
                output.append(f"   Description: {change.get('description', 'No description')}")
        
        output.append(f"\n⚠️ Priority: {request['priority'].upper()}")
        output.append(f"\n🤔 Would you like to proceed with these changes?")
        output.append(f"   Confirmation ID: {request['id']}")
        output.append(f"\n   Reply with: 'yes {request['id']}' or 'no {request['id']}'")
        
        return "\n".join(output)
    
    def confirm(self, request_id: str) -> bool:
        """Mark recommendation as confirmed.
        
        Args:
            request_id: ID of the confirmation request
            
        Returns:
            True if confirmed successfully
        """
        if request_id in self.pending_recommendations:
            self.pending_recommendations[request_id]["status"] = "confirmed"
            return True
        return False
    
    def reject(self, request_id: str) -> bool:
        """Mark recommendation as rejected.
        
        Args:
            request_id: ID of the confirmation request
            
        Returns:
            True if rejected successfully
        """
        if request_id in self.pending_recommendations:
            self.pending_recommendations[request_id]["status"] = "rejected"
            return True
        return False
    
    def get_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get confirmation request by ID.
        
        Args:
            request_id: ID of the request
            
        Returns:
            Request dict or None
        """
        return self.pending_recommendations.get(request_id)
    
    def get_pending_requests(self) -> List[Dict[str, Any]]:
        """Get all pending confirmation requests.
        
        Returns:
            List of pending requests
        """
        return [
            req for req in self.pending_recommendations.values()
            if req["status"] == "pending"
        ]
    
    def clear_completed(self):
        """Remove completed (confirmed/rejected) requests."""
        self.pending_recommendations = {
            req_id: req for req_id, req in self.pending_recommendations.items()
            if req["status"] == "pending"
        }


# Global instance
_confirmation_manager = None


def get_confirmation_manager() -> RecommendationConfirmation:
    """Get or create global confirmation manager instance."""
    global _confirmation_manager
    if _confirmation_manager is None:
        _confirmation_manager = RecommendationConfirmation()
    return _confirmation_manager
