import os
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from utils.logger import logger

class TwilioCallManager:
    """Manages Twilio voice calls for the AI sales agent"""
    
    def __init__(self):
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.phone_number = os.getenv('TWILIO_PHONE_NUMBER')
        
        if not all([self.account_sid, self.auth_token, self.phone_number]):
            raise ValueError("Missing required Twilio environment variables")
        
        self.client = Client(self.account_sid, self.auth_token)
        self.webhook_base_url = os.getenv('WEBHOOK_BASE_URL')
        if not self.webhook_base_url:
            raise ValueError("Missing WEBHOOK_BASE_URL environment variable")
    
    def initiate_call(self, lead_phone, lead_id, lead_name=""):
        """Initiate a voice call to a lead"""
        try:
            # Format phone number (remove spaces, add + if needed)
            formatted_phone = self._format_phone_number(lead_phone)
            
            # Build webhook URL with lead context
            webhook_url = f"{self.webhook_base_url}/twilio/voice/{lead_id}"
            
            # Call parameters
            call_params = {
                'to': formatted_phone,
                'from_': self.phone_number,
                'url': webhook_url,
                'method': 'POST',
                'status_callback': f"{self.webhook_base_url}/twilio/status",
                'status_callback_event': ['initiated', 'ringing', 'answered', 'completed'],
                'status_callback_method': 'POST',
                'record': True,  # Record the call for analysis
                'recording_status_callback': f"{self.webhook_base_url}/twilio/recording",
                'recording_status_callback_method': 'POST'
            }
            
            # Make the call
            call = self.client.calls.create(**call_params)
            
            logger.log_call_start(lead_id, formatted_phone)
            logger.info(f"Initiated Twilio call to {lead_name} ({formatted_phone}) - Call SID: {call.sid}")
            
            return {
                'call_sid': call.sid,
                'status': call.status,
                'to': formatted_phone,
                'lead_id': lead_id
            }
            
        except TwilioException as e:
            logger.error(f"Twilio error initiating call to {lead_phone}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error initiating call to {lead_phone}: {str(e)}")
            return None
    
    def _format_phone_number(self, phone):
        """Format phone number for Twilio"""
        # Remove all non-digit characters except +
        cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')
        
        # If no + prefix, add appropriate country code
        if not cleaned.startswith('+'):
            if cleaned.startswith('91') and len(cleaned) == 12:
                cleaned = '+' + cleaned
            elif cleaned.startswith('03') and len(cleaned) == 11:  # Pakistani number
                cleaned = '+92' + cleaned[1:]  # Remove leading 0, add +92
            elif len(cleaned) == 10:  # Indian mobile number
                cleaned = '+91' + cleaned
            elif len(cleaned) == 11 and cleaned.startswith('0'):  # Any 11-digit number starting with 0
                cleaned = '+92' + cleaned[1:]  # Assume Pakistani, remove leading 0, add +92
            else:
                cleaned = '+' + cleaned
        
        return cleaned
    
    def get_call_status(self, call_sid):
        """Get the current status of a call"""
        try:
            call = self.client.calls(call_sid).fetch()
            return {
                'sid': call.sid,
                'status': call.status,
                'duration': call.duration,
                'start_time': call.start_time,
                'end_time': call.end_time,
                'price': call.price,
                'price_unit': call.price_unit
            }
        except TwilioException as e:
            logger.error(f"Failed to get call status for {call_sid}: {str(e)}")
            return None
    
    def end_call(self, call_sid):
        """End an active call"""
        try:
            call = self.client.calls(call_sid).update(status='completed')
            logger.info(f"Ended call {call_sid}")
            return True
        except TwilioException as e:
            logger.error(f"Failed to end call {call_sid}: {str(e)}")
            return False
    
    def get_call_logs(self, limit=50):
        """Get recent call logs"""
        try:
            calls = self.client.calls.list(limit=limit)
            return [
                {
                    'sid': call.sid,
                    'to': call.to,
                    'from_': call.from_formatted,
                    'status': call.status,
                    'start_time': call.start_time,
                    'duration': call.duration,
                    'price': call.price
                }
                for call in calls
            ]
        except TwilioException as e:
            logger.error(f"Failed to get call logs: {str(e)}")
            return []
    
    def test_connection(self):
        """Test Twilio connection by fetching account info"""
        try:
            account = self.client.api.accounts(self.account_sid).fetch()
            logger.info(f"Twilio connection test successful - Account: {account.friendly_name}")
            return True
        except Exception as e:
            logger.error(f"Twilio connection test failed: {str(e)}")
            return False



