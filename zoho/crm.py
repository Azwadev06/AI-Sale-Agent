import os
import requests
import json
from datetime import datetime
from .auth import ZohoAuth
from utils.logger import logger

class ZohoCRM:
    """Handles Zoho CRM operations for leads"""
    
    def __init__(self):
        self.auth = ZohoAuth()
        self.dc = os.getenv('ZOHO_DC', 'com')
        self.base_url = f"https://www.zohoapis.com/crm/v3"
    
    def get_leads(self, status="New", limit=10):
        """Fetch leads with specified status"""
        try:
            url = f"{self.base_url}/Leads"
            
            # Build query parameters
            params = {
                'fields': 'id,Lead_Owner,Company,First_Name,Last_Name,Phone,Email,Lead_Status,Lead_Source,Industry,Annual_Revenue,No_of_Employees,Description',
                'per_page': limit
            }
            
            if status:
                params['crm_details'] = 'true'
                # Use search criteria for status
                search_criteria = f'(Lead_Status:equals:{status})'
                params['search_criteria'] = search_criteria
            
            headers = self.auth.get_headers()
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            leads = data.get('data', [])
            
            logger.info(f"Successfully fetched {len(leads)} leads with status '{status}'")
            return leads
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch leads: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching leads: {str(e)}")
            return []
    
    def get_lead_by_id(self, lead_id):
        """Fetch a specific lead by ID"""
        try:
            url = f"{self.base_url}/Leads/{lead_id}"
            headers = self.auth.get_headers()
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            lead = data.get('data', [{}])[0]
            
            logger.info(f"Successfully fetched lead ID: {lead_id}")
            return lead
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch lead {lead_id}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching lead {lead_id}: {str(e)}")
            return None
    
    def update_lead(self, lead_id, update_data):
        """Update a lead with new data"""
        try:
            url = f"{self.base_url}/Leads/{lead_id}"
            headers = self.auth.get_headers()
            
            # Prepare data for update
            payload = {
                "data": [update_data]
            }
            
            response = requests.put(url, headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            if data.get('status', {}).get('code') == 'SUCCESS':
                logger.info(f"Successfully updated lead ID: {lead_id}")
                return True
            else:
                logger.error(f"Failed to update lead {lead_id}: {data.get('status', {}).get('message')}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update lead {lead_id}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating lead {lead_id}: {str(e)}")
            return False
    
    def mark_lead_qualified(self, lead_id, qualification_summary, conversation_notes=""):
        """Mark a lead as qualified and add conversation summary"""
        update_data = {
            "Lead_Status": "Qualified",
            "Description": f"AI Qualification Summary: {qualification_summary}\n\nConversation Notes: {conversation_notes}",
            "Last_Activity_Time": datetime.now().isoformat()
        }
        
        success = self.update_lead(lead_id, update_data)
        if success:
            logger.log_zoho_operation("UPDATE", lead_id, "Qualified")
        return success
    
    def mark_lead_disqualified(self, lead_id, disqualification_reason, conversation_notes=""):
        """Mark a lead as disqualified and add reason"""
        update_data = {
            "Lead_Status": "Disqualified",
            "Description": f"AI Disqualification Reason: {disqualification_reason}\n\nConversation Notes: {conversation_notes}",
            "Last_Activity_Time": datetime.now().isoformat()
        }
        
        success = self.update_lead(lead_id, update_data)
        if success:
            logger.log_zoho_operation("UPDATE", lead_id, "Disqualified")
        return success
    
    def add_conversation_notes(self, lead_id, notes):
        """Add conversation notes to a lead"""
        # First get current description
        current_lead = self.get_lead_by_id(lead_id)
        if not current_lead:
            return False
        
        current_description = current_lead.get('Description', '')
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        new_description = f"{current_description}\n\n[{timestamp}] {notes}"
        
        update_data = {
            "Description": new_description,
            "Last_Activity_Time": datetime.now().isoformat()
        }
        
        return self.update_lead(lead_id, update_data)
    
    def get_next_lead_for_call(self):
        """Get the next available lead for calling"""
        leads = self.get_leads(status="New", limit=1)
        if leads:
            lead = leads[0]
            logger.info(f"Selected lead for call: {lead.get('First_Name', 'Unknown')} {lead.get('Last_Name', '')} - {lead.get('Phone', 'No Phone')}")
            return lead
        else:
            logger.info("No new leads available for calling")
            return None
    
    def test_connection(self):
        """Test the CRM connection"""
        try:
            leads = self.get_leads(limit=1)
            logger.info("Zoho CRM connection test successful")
            return True
        except Exception as e:
            logger.error(f"Zoho CRM connection test failed: {str(e)}")
            return False

