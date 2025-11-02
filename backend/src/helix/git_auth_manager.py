"""Git authentication manager supporting multiple authentication methods.

Supports:
- Option A: Local git credential helper / VS Code Git extension
- Option B: Personal Access Tokens (PATs) stored securely
- Option C: OAuth flow for GitHub authentication
"""
from typing import Dict, List, Any, Optional
import subprocess
import os
import json
from pathlib import Path
from enum import Enum


class AuthMethod(Enum):
    """Supported authentication methods."""
    CREDENTIAL_HELPER = "credential_helper"
    PAT = "personal_access_token"
    OAUTH = "oauth"


class GitAuthManager:
    """Manages Git authentication across multiple methods and accounts."""
    
    def __init__(self, workspace_dir: str):
        """Initialize the Git authentication manager.
        
        Args:
            workspace_dir: Root directory of the repository
        """
        self.workspace_dir = Path(workspace_dir)
        self.config_file = self.workspace_dir / '.helix' / 'git_auth.json'
        self._ensure_config_dir()
    
    def _ensure_config_dir(self):
        """Ensure .helix directory exists."""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
    
    def get_available_accounts(self) -> Dict[str, Any]:
        """Get all available Git accounts across all authentication methods.
        
        Returns:
            Dictionary with accounts grouped by auth method
        """
        accounts = {
            'credential_helper': self._get_credential_helper_accounts(),
            'pat': self._get_stored_pats(),
            'oauth': self._get_oauth_accounts()
        }
        
        return {
            'ok': True,
            'accounts': accounts,
            'total_count': sum(len(accts) for accts in accounts.values())
        }
    
    def _get_credential_helper_accounts(self) -> List[Dict[str, str]]:
        """Get accounts from local git config (credential helper).
        
        Returns:
            List of account dictionaries with name, email, and source
        """
        accounts = []
        
        try:
            # Get global git config
            result = subprocess.run(
                ['git', 'config', '--list'],
                cwd=self.workspace_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                config_lines = result.stdout.strip().split('\n')
                
                # Parse user.name and user.email
                name = None
                email = None
                
                for line in config_lines:
                    if '=' in line:
                        key, value = line.split('=', 1)
                        if key == 'user.name':
                            name = value
                        elif key == 'user.email':
                            email = value
                
                if name or email:
                    accounts.append({
                        'name': name or 'Unknown',
                        'email': email or 'Unknown',
                        'source': 'git_config',
                        'auth_method': 'credential_helper',
                        'available': True
                    })
            
            # Check for credential helper
            cred_result = subprocess.run(
                ['git', 'config', 'credential.helper'],
                cwd=self.workspace_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if cred_result.returncode == 0 and cred_result.stdout.strip():
                if accounts:
                    accounts[0]['credential_helper'] = cred_result.stdout.strip()
        
        except Exception as e:
            print(f"⚠️ Error reading git config: {str(e)}")
        
        return accounts
    
    def _get_stored_pats(self) -> List[Dict[str, str]]:
        """Get stored Personal Access Tokens from config file.
        
        Returns:
            List of PAT account dictionaries
        """
        if not self.config_file.exists():
            return []
        
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            pats = config.get('pats', [])
            
            # Return list with masked tokens
            return [
                {
                    'name': pat.get('name', 'Unknown'),
                    'username': pat.get('username', 'Unknown'),
                    'email': pat.get('email'),
                    'token_preview': pat.get('token', '')[:8] + '...' if pat.get('token') else 'Not set',
                    'source': 'stored_pat',
                    'auth_method': 'pat',
                    'available': True,
                    'created_at': pat.get('created_at')
                }
                for pat in pats
            ]
        
        except Exception as e:
            print(f"⚠️ Error reading stored PATs: {str(e)}")
            return []
    
    def _get_oauth_accounts(self) -> List[Dict[str, str]]:
        """Get OAuth-authenticated accounts.
        
        Returns:
            List of OAuth account dictionaries
        """
        if not self.config_file.exists():
            return []
        
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            oauth_accounts = config.get('oauth', [])
            
            return [
                {
                    'name': acc.get('name', 'Unknown'),
                    'username': acc.get('username', 'Unknown'),
                    'email': acc.get('email'),
                    'avatar_url': acc.get('avatar_url'),
                    'source': 'oauth',
                    'auth_method': 'oauth',
                    'available': True,
                    'expires_at': acc.get('expires_at')
                }
                for acc in oauth_accounts
            ]
        
        except Exception as e:
            print(f"⚠️ Error reading OAuth accounts: {str(e)}")
            return []
    
    def store_pat(self, name: str, username: str, token: str, email: Optional[str] = None) -> Dict[str, Any]:
        """Store a Personal Access Token.
        
        Args:
            name: Display name for the account
            username: GitHub username
            token: GitHub Personal Access Token
            email: Optional email address
            
        Returns:
            Success status and message
        """
        try:
            # Load existing config
            config = {}
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
            
            if 'pats' not in config:
                config['pats'] = []
            
            # Add new PAT
            from datetime import datetime
            config['pats'].append({
                'name': name,
                'username': username,
                'email': email,
                'token': token,
                'created_at': datetime.now().isoformat()
            })
            
            # Save config
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            # Set restrictive permissions (only owner can read/write)
            os.chmod(self.config_file, 0o600)
            
            return {
                'ok': True,
                'message': f'PAT stored for {username}',
                'name': name
            }
        
        except Exception as e:
            return {
                'ok': False,
                'error': f'Failed to store PAT: {str(e)}'
            }
    
    def store_oauth_token(self, name: str, username: str, access_token: str, 
                          refresh_token: Optional[str] = None, 
                          email: Optional[str] = None,
                          avatar_url: Optional[str] = None,
                          expires_in: Optional[int] = None) -> Dict[str, Any]:
        """Store OAuth authentication tokens.
        
        Args:
            name: Display name for the account
            username: GitHub username
            access_token: OAuth access token
            refresh_token: Optional refresh token
            email: Optional email address
            avatar_url: Optional avatar URL
            expires_in: Token expiration time in seconds
            
        Returns:
            Success status and message
        """
        try:
            # Load existing config
            config = {}
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
            
            if 'oauth' not in config:
                config['oauth'] = []
            
            # Calculate expiration
            from datetime import datetime, timedelta
            expires_at = None
            if expires_in:
                expires_at = (datetime.now() + timedelta(seconds=expires_in)).isoformat()
            
            # Add new OAuth account
            config['oauth'].append({
                'name': name,
                'username': username,
                'email': email,
                'avatar_url': avatar_url,
                'access_token': access_token,
                'refresh_token': refresh_token,
                'expires_at': expires_at,
                'created_at': datetime.now().isoformat()
            })
            
            # Save config
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            # Set restrictive permissions
            os.chmod(self.config_file, 0o600)
            
            return {
                'ok': True,
                'message': f'OAuth token stored for {username}',
                'name': name
            }
        
        except Exception as e:
            return {
                'ok': False,
                'error': f'Failed to store OAuth token: {str(e)}'
            }
    
    def get_credentials_for_push(self, account_identifier: str, auth_method: str) -> Dict[str, Any]:
        """Get credentials for a specific account to perform push operation.
        
        Args:
            account_identifier: Email, username, or account name
            auth_method: One of 'credential_helper', 'pat', or 'oauth'
            
        Returns:
            Credentials dictionary with auth details
        """
        if auth_method == 'credential_helper':
            return self._get_credential_helper_creds(account_identifier)
        elif auth_method == 'pat':
            return self._get_pat_creds(account_identifier)
        elif auth_method == 'oauth':
            return self._get_oauth_creds(account_identifier)
        else:
            return {
                'ok': False,
                'error': f'Unknown auth method: {auth_method}'
            }
    
    def _get_credential_helper_creds(self, identifier: str) -> Dict[str, Any]:
        """Get credentials using git credential helper."""
        return {
            'ok': True,
            'auth_method': 'credential_helper',
            'use_system_git': True,
            'message': 'Using system git credential helper'
        }
    
    def _get_pat_creds(self, identifier: str) -> Dict[str, Any]:
        """Get PAT credentials for the specified account."""
        try:
            if not self.config_file.exists():
                return {'ok': False, 'error': 'No stored PATs found'}
            
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            pats = config.get('pats', [])
            
            # Find matching PAT
            for pat in pats:
                if (pat.get('username') == identifier or 
                    pat.get('email') == identifier or 
                    pat.get('name') == identifier):
                    return {
                        'ok': True,
                        'auth_method': 'pat',
                        'username': pat.get('username'),
                        'token': pat.get('token'),
                        'email': pat.get('email')
                    }
            
            return {'ok': False, 'error': f'No PAT found for {identifier}'}
        
        except Exception as e:
            return {'ok': False, 'error': str(e)}
    
    def _get_oauth_creds(self, identifier: str) -> Dict[str, Any]:
        """Get OAuth credentials for the specified account."""
        try:
            if not self.config_file.exists():
                return {'ok': False, 'error': 'No OAuth accounts found'}
            
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            oauth_accounts = config.get('oauth', [])
            
            # Find matching OAuth account
            for acc in oauth_accounts:
                if (acc.get('username') == identifier or 
                    acc.get('email') == identifier or 
                    acc.get('name') == identifier):
                    
                    # Check if token is expired
                    from datetime import datetime
                    expires_at = acc.get('expires_at')
                    if expires_at:
                        if datetime.fromisoformat(expires_at) < datetime.now():
                            return {'ok': False, 'error': 'OAuth token expired', 'needs_refresh': True}
                    
                    return {
                        'ok': True,
                        'auth_method': 'oauth',
                        'username': acc.get('username'),
                        'access_token': acc.get('access_token'),
                        'email': acc.get('email')
                    }
            
            return {'ok': False, 'error': f'No OAuth account found for {identifier}'}
        
        except Exception as e:
            return {'ok': False, 'error': str(e)}
    
    def remove_account(self, identifier: str, auth_method: str) -> Dict[str, Any]:
        """Remove a stored account.
        
        Args:
            identifier: Account identifier (username, email, or name)
            auth_method: 'pat' or 'oauth' (credential_helper can't be removed)
            
        Returns:
            Success status and message
        """
        if auth_method not in ['pat', 'oauth']:
            return {'ok': False, 'error': 'Can only remove PAT or OAuth accounts'}
        
        try:
            if not self.config_file.exists():
                return {'ok': False, 'error': 'No config file found'}
            
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            key = 'pats' if auth_method == 'pat' else 'oauth'
            accounts = config.get(key, [])
            
            # Filter out the account
            original_count = len(accounts)
            config[key] = [
                acc for acc in accounts
                if not (acc.get('username') == identifier or 
                       acc.get('email') == identifier or 
                       acc.get('name') == identifier)
            ]
            
            if len(config[key]) == original_count:
                return {'ok': False, 'error': f'Account {identifier} not found'}
            
            # Save updated config
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            return {
                'ok': True,
                'message': f'Account {identifier} removed'
            }
        
        except Exception as e:
            return {'ok': False, 'error': str(e)}
