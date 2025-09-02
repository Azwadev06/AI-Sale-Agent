#!/usr/bin/env python3
"""
AI Voice Sales Agent - Main Orchestrator
Integrates Zoho CRM, Twilio Voice, and OpenAI GPT-4 for automated lead qualification
"""

import os
import sys
import time
import argparse
import threading
import subprocess
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Import project modules
from zoho.crm import ZohoCRM
from twilio_directory.call import TwilioCallManager
from gpt.agent import GPTAgent
from utils.logger import logger

class AIVoiceSalesAgent:
    """Main orchestrator for the AI Voice Sales Agent"""
    
    def __init__(self):
        """Initialize all components"""
        try:
            logger.info("Initializing AI Voice Sales Agent...")
            
            # Initialize components
            self.crm = ZohoCRM()
            self.twilio = TwilioCallManager()
            self.gpt = GPTAgent()
            
            # Start webhook server in background
            self.start_webhook_server()
            
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {str(e)}")
            raise
    
    def start_webhook_server(self):
        """Start the webhook server in background"""
        try:
            def run_webhook():
                from twilio_directory.webhook import app
                app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
            
            webhook_thread = threading.Thread(target=run_webhook, daemon=True)
            webhook_thread.start()
            time.sleep(2)  # Give server time to start
            logger.info("✅ Webhook server started on port 5000")
            
        except Exception as e:
            logger.warning(f"Could not start webhook server: {e}")
            logger.warning("Make sure to run webhook server manually for call handling")
    
    def test_connections(self):
        """Test all external service connections"""
        logger.info("Testing external service connections...")
        
        results = {
            'zoho': False,
            'twilio': False,
            'openai': False
        }
        
        # Test Zoho CRM
        try:
            results['zoho'] = self.crm.test_connection()
        except Exception as e:
            logger.error(f"Zoho CRM test failed: {str(e)}")
        
        # Test Twilio
        try:
            results['twilio'] = self.twilio.test_connection()
        except Exception as e:
            logger.error(f"Twilio test failed: {str(e)}")
        
        # Test OpenAI
        try:
            results['openai'] = self.gpt.test_connection()
        except Exception as e:
            logger.error(f"OpenAI test failed: {str(e)}")
        
        # Log results
        for service, status in results.items():
            if status:
                logger.info(f"✅ {service.upper()} connection successful")
            else:
                logger.error(f"❌ {service.upper()} connection failed")
        
        return all(results.values())
    
    def get_next_lead(self):
        """Get the next available lead for calling"""
        try:
            lead = self.crm.get_next_lead_for_call()
            if lead:
                logger.info(f"Next lead: {lead.get('First_Name', 'Unknown')} {lead.get('Last_Name', '')} - {lead.get('Phone', 'No Phone')}")
                return lead
            else:
                logger.info("No leads available for calling")
                return None
        except Exception as e:
            logger.error(f"Error getting next lead: {str(e)}")
            return None
    
    def initiate_call(self, lead):
        """Initiate a call to a lead"""
        try:
            lead_id = lead.get('id')
            phone = lead.get('Phone')
            name = f"{lead.get('First_Name', '')} {lead.get('Last_Name', '')}".strip()
            
            if not phone:
                logger.error(f"Lead {lead_id} has no phone number")
                return False
            
            logger.info(f"Initiating call to {name} ({phone})")
            
            # Start the call
            call_result = self.twilio.initiate_call(phone, lead_id, name)
            
            if call_result:
                logger.info(f"Call initiated successfully - SID: {call_result['call_sid']}")
                return True
            else:
                logger.error("Failed to initiate call")
                return False
                
        except Exception as e:
            logger.error(f"Error initiating call: {str(e)}")
            return False
    
    def run_automated_campaign(self, max_calls=5, delay_minutes=5):
        """Run automated campaign calling multiple leads"""
        logger.info(f"Starting automated campaign - Max calls: {max_calls}, Delay: {delay_minutes} minutes")
        
        calls_made = 0
        
        while calls_made < max_calls:
            try:
                # Get next lead
                lead = self.get_next_lead()
                if not lead:
                    logger.info("No more leads available, ending campaign")
                    break
                
                # Initiate call
                if self.initiate_call(lead):
                    calls_made += 1
                    logger.info(f"Call {calls_made}/{max_calls} initiated successfully")
                    
                    # Wait before next call
                    if calls_made < max_calls:
                        logger.info(f"Waiting {delay_minutes} minutes before next call...")
                        time.sleep(delay_minutes * 60)
                else:
                    logger.warning(f"Failed to initiate call for lead {lead.get('id')}")
                    time.sleep(60)  # Wait 1 minute before retry
                    
            except KeyboardInterrupt:
                logger.info("Campaign interrupted by user")
                break
            except Exception as e:
                logger.error(f"Error in campaign: {str(e)}")
                time.sleep(60)  # Wait 1 minute before retry
        
        logger.info(f"Campaign completed. Total calls made: {calls_made}")
        return calls_made
    
    def test_lead_fetch(self):
        """Test fetching leads from Zoho CRM"""
        logger.info("Testing lead fetch from Zoho CRM...")
        
        try:
            leads = self.crm.get_leads(status="New", limit=5)
            
            if leads:
                logger.info(f"Successfully fetched {len(leads)} leads:")
                for i, lead in enumerate(leads, 1):
                    name = f"{lead.get('First_Name', 'Unknown')} {lead.get('Last_Name', '')}".strip()
                    phone = lead.get('Phone', 'No Phone')
                    company = lead.get('Company', 'No Company')
                    
                    logger.info(f"  {i}. {name} - {phone} - {company}")
            else:
                logger.info("No leads found")
                
            return True
            
        except Exception as e:
            logger.error(f"Lead fetch test failed: {str(e)}")
            return False
    
    def test_lead_update(self, lead_id):
        """Test updating a lead in Zoho CRM"""
        logger.info(f"Testing lead update for ID: {lead_id}")
        
        try:
            # Test adding conversation notes
            test_notes = f"Test conversation notes - {datetime.now().isoformat()}"
            success = self.crm.add_conversation_notes(lead_id, test_notes)
            
            if success:
                logger.info("Lead update test successful")
                return True
            else:
                logger.error("Lead update test failed")
                return False
                
        except Exception as e:
            logger.error(f"Lead update test failed: {str(e)}")
            return False
    
    def show_system_status(self):
        """Show current system status"""
        logger.info("=== AI Voice Sales Agent - System Status ===")
        
        # Test connections
        connections_ok = self.test_connections()
        
        if connections_ok:
            logger.info("✅ All services connected")
            
            # Show recent leads
            leads = self.crm.get_leads(limit=3)
            if leads:
                logger.info(f"📊 Recent leads: {len(leads)} available")
            else:
                logger.info("📊 No leads available")
            
            # Show recent calls
            calls = self.twilio.get_call_logs(limit=3)
            if calls:
                logger.info(f"📞 Recent calls: {len(calls)} made")
            else:
                logger.info("📞 No recent calls")
                
        else:
            logger.error("❌ Some services are not connected")
        
        logger.info("==========================================")

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description='AI Voice Sales Agent')
    parser.add_argument('--test', action='store_true', help='Test all connections')
    parser.add_argument('--status', action='store_true', help='Show system status')
    parser.add_argument('--fetch-leads', action='store_true', help='Test fetching leads')
    parser.add_argument('--update-lead', type=str, help='Test updating a specific lead ID')
    parser.add_argument('--call-lead', type=str, help='Initiate call to a specific lead ID')
    parser.add_argument('--campaign', type=int, metavar='MAX_CALLS', help='Run automated campaign with max calls')
    parser.add_argument('--delay', type=int, default=5, help='Delay between calls in minutes (default: 5)')
    
    args = parser.parse_args()
    
    try:
        # Initialize the agent
        agent = AIVoiceSalesAgent()
        
        if args.test:
            logger.info("Running connection tests...")
            success = agent.test_connections()
            sys.exit(0 if success else 1)
        
        elif args.status:
            agent.show_system_status()
        
        elif args.fetch_leads:
            success = agent.test_lead_fetch()
            sys.exit(0 if success else 1)
        
        elif args.update_lead:
            success = agent.test_lead_update(args.update_lead)
            sys.exit(0 if success else 1)
        
        elif args.call_lead:
            lead = agent.crm.get_lead_by_id(args.call_lead)
            if lead:
                success = agent.initiate_call(lead)
                sys.exit(0 if success else 1)
            else:
                logger.error(f"Lead {args.call_lead} not found")
                sys.exit(1)
        
        elif args.campaign:
            logger.info(f"Starting automated campaign with max {args.campaign} calls...")
            calls_made = agent.run_automated_campaign(args.campaign, args.delay)
            logger.info(f"Campaign completed. Calls made: {calls_made}")
        
        else:
            # Default: automatically get lead and make call
            logger.info("🚀 AI Voice Sales Agent - Auto Mode")
            logger.info("=" * 50)
            
            # Test connections first
            if not agent.test_connections():
                logger.error("❌ Connection test failed. Please check your credentials.")
                sys.exit(1)
            
            # Get next lead
            lead = agent.get_next_lead()
            if not lead:
                logger.error("❌ No leads available for calling")
                sys.exit(1)
            
            # Make the call
            logger.info(f"📞 Making call to: {lead.get('First_Name', 'Unknown')} {lead.get('Last_Name', '')}")
            success = agent.initiate_call(lead)
            
            if success:
                logger.info("✅ Call initiated successfully!")
                logger.info("🤖 AI agent will handle the conversation via webhooks")
                logger.info("📊 Results will be written back to Zoho CRM")
            else:
                logger.error("❌ Failed to initiate call")
                sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()



