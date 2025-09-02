import os
import requests
import json
from datetime import datetime, timedelta
from utils.logger import logger

class ZohoAuth:
    """Handles Zoho CRM OAuth2 authentication"""
    
    def __init__(self):
        self.client_id = os.getenv('ZOHO_CLIENT_ID')
        self.client_secret = os.getenv('ZOHO_CLIENT_SECRET')
        self.refresh_token = os.getenv('ZOHO_REFRESH_TOKEN')
        self.redirect_uri = os.getenv('ZOHO_REDIRECT_URI')
        self.dc = os.getenv('ZOHO_DC', 'com')  # Data center
        
        if not all([self.client_id, self.client_secret, self.refresh_token]):
            raise ValueError("Missing required Zoho environment variables")
        
        self.base_url = f"https://accounts.zoho.{self.dc}"
        self.access_token = None
        self.token_expiry = None
    
    def get_access_token(self):
        """Get a valid access token, refreshing if necessary"""
        if self._is_token_valid():
            return self.access_token
        
        return self._refresh_access_token()
    
    def _is_token_valid(self):
        """Check if current access token is still valid"""
        if not self.access_token or not self.token_expiry:
            return False
        
        # Add 5 minute buffer before expiry
        buffer_time = datetime.now() + timedelta(minutes=5)
        return self.token_expiry > buffer_time
    
    def _refresh_access_token(self):
        """Refresh the access token using refresh token"""
        try:
            url = f"{self.base_url}/oauth/v2/token"
            data = {
                'refresh_token': self.refresh_token,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': 'refresh_token'
            }
            
            response = requests.post(url, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            
            # Set expiry time (Zoho tokens typically last 1 hour)
            expiry_seconds = token_data.get('expires_in', 3600)
            self.token_expiry = datetime.now() + timedelta(seconds=expiry_seconds)
            
            logger.info("Successfully refreshed Zoho access token")
            return self.access_token
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to refresh Zoho access token: {str(e)}")
            raise
    
    def get_headers(self):
        """Get headers with valid access token for API requests"""
        return {
            'Authorization': f'Zoho-oauthtoken {self.get_access_token()}',
            'Content-Type': 'application/json'
        }
    
    def test_connection(self):
        """Test the Zoho connection by making a simple API call"""
        try:
            from .crm import ZohoCRM
            crm = ZohoCRM()
            # Try to fetch a single lead to test connection
            leads = crm.get_leads(limit=1)
            if leads:
                logger.info("Zoho CRM connection test successful")
                return True
            else:
                logger.warning("Zoho CRM connection test: No leads found")
                return True
        except Exception as e:
            logger.error(f"Zoho CRM connection test failed: {str(e)}")
            return False
