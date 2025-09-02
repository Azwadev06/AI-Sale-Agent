from flask import Flask, request, Response
from twilio.twiml.voice_response import VoiceResponse, Gather
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from gpt.agent import GPTAgent
from zoho.crm import ZohoCRM
from utils.logger import logger

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')
if not app.secret_key:
    raise ValueError("Missing FLASK_SECRET_KEY environment variable")

# Initialize components
gpt_agent = GPTAgent()
crm = ZohoCRM()

# In-memory storage for conversation state (in production, use Redis/database)
conversation_states = {}

@app.route('/')
def health_check():
    """Health check endpoint"""
    return "AI Voice Sales Agent Webhook Server is running"

@app.route('/test')
def test_endpoint():
    """Test endpoint"""
    return {
        "status": "ok",
        "message": "Webhook server is working",
        "timestamp": datetime.now().isoformat()
    }

@app.route('/twilio/voice/<lead_id>', methods=['POST'])
def handle_voice_webhook(lead_id):
    """Handle incoming voice calls from Twilio"""
    try:
        # Get call details from Twilio
        call_sid = request.form.get('CallSid')
        from_number = request.form.get('From')
        to_number = request.form.get('To')
        
        logger.info(f"Voice webhook received for Lead {lead_id}, Call SID: {call_sid}")
        logger.info(f"Call from: {from_number}, to: {to_number}")
        
        # Initialize conversation state for this lead
        if lead_id not in conversation_states:
            conversation_states[lead_id] = {
                'lead_id': lead_id,
                'call_sid': call_sid,
                'conversation_history': [],
                'current_step': 'greeting',
                'start_time': datetime.now().isoformat(),
                'qualification_questions': []
            }
        
        # Get lead information from Zoho
        try:
            lead_info = crm.get_lead_by_id(lead_id)
            if not lead_info:
                logger.error(f"Lead {lead_id} not found in Zoho CRM")
                return _generate_error_response("Lead information not found")
        except Exception as e:
            logger.error(f"Error fetching lead {lead_id}: {e}")
            return _generate_error_response("Error fetching lead information")
        
        # Generate TwiML response
        twiml = _generate_voice_response(lead_id, lead_info)
        
        logger.info(f"Generated TwiML response for Lead {lead_id}")
        return Response(str(twiml), mimetype='text/xml')
        
    except Exception as e:
        logger.error(f"Error in voice webhook for Lead {lead_id}: {str(e)}")
        return _generate_error_response("An error occurred")

@app.route('/twilio/gather', methods=['POST'])
def handle_gather():
    """Handle speech input from the user"""
    try:
        lead_id = request.form.get('lead_id')
        speech_result = request.form.get('SpeechResult', '')
        confidence = request.form.get('Confidence', '0')
        
        logger.info(f"Speech input received for Lead {lead_id}: '{speech_result}' (confidence: {confidence})")
        
        if not lead_id or lead_id not in conversation_states:
            return _generate_error_response("Invalid lead ID")
        
        # Add user response to conversation history
        conversation_states[lead_id]['conversation_history'].append({
            'speaker': 'user',
            'message': speech_result,
            'confidence': confidence,
            'timestamp': datetime.now().isoformat()
        })
        
        # Use GPT to determine next question or qualification
        next_response = gpt_agent.process_user_response(
            lead_id, 
            speech_result, 
            conversation_states[lead_id]
        )
        
        # Generate TwiML response
        twiml = _generate_follow_up_response(lead_id, next_response)
        
        return Response(str(twiml), mimetype='text/xml')
        
    except Exception as e:
        logger.error(f"Error handling gather input: {str(e)}")
        return _generate_error_response("An error occurred")

@app.route('/twilio/status', methods=['POST'])
def handle_call_status():
    """Handle call status updates from Twilio"""
    try:
        call_sid = request.form.get('CallSid')
        call_status = request.form.get('CallStatus')
        call_duration = request.form.get('CallDuration')
        
        logger.info(f"Call status update: {call_sid} - {call_status} (Duration: {call_duration}s)")
        
        # Find lead_id from conversation states
        lead_id = None
        for lid, state in conversation_states.items():
            if state.get('call_sid') == call_sid:
                lead_id = lid
                break
        
        if lead_id and call_status == 'completed':
            # Process final qualification
            _process_final_qualification(lead_id)
        
        return Response('OK', status=200)
        
    except Exception as e:
        logger.error(f"Error handling call status: {str(e)}")
        return Response('Error', status=500)

@app.route('/twilio/recording', methods=['POST'])
def handle_recording():
    """Handle recording status updates"""
    try:
        call_sid = request.form.get('CallSid')
        recording_url = request.form.get('RecordingUrl')
        recording_status = request.form.get('RecordingStatus')
        
        logger.info(f"Recording update: {call_sid} - {recording_status}")
        
        if recording_url:
            logger.info(f"Recording available at: {recording_url}")
        
        return Response('OK', status=200)
        
    except Exception as e:
        logger.error(f"Error handling recording: {str(e)}")
        return Response('Error', status=500)

def _generate_voice_response(lead_id, lead_info):
    """Generate initial voice response with greeting"""
    response = VoiceResponse()
    
    # Get lead name
    first_name = lead_info.get('First_Name', '')
    last_name = lead_info.get('Last_Name', '')
    company = lead_info.get('Company', '')
    
    lead_name = f"{first_name} {last_name}".strip()
    if not lead_name:
        lead_name = "Sir/Madam"
    
    # Greeting message in Hindi
    greeting = f"Namaste {lead_name}! Main aapko call kar raha hoon. Kya aap mujhe 2 minute de sakte hain?"
    
    # Use Hindi voice (Aditi)
    response.say(greeting, voice='Polly.Aditi', language='hi-IN')
    
    # Gather speech input
    gather = response.gather(
        input='speech',
        language='hi-IN',
        speech_timeout='auto',
        action=f'/twilio/gather?lead_id={lead_id}',
        method='POST'
    )
    
    # Fallback if no speech detected
    gather.say("Aap kuch bol sakte hain?", voice='Polly.Aditi', language='hi-IN')
    
    # If no input, end call gracefully
    response.say("Thank you for your time. Goodbye!", voice='Polly.Aditi', language='hi-IN')
    response.hangup()
    
    return response

def _generate_follow_up_response(lead_id, gpt_response):
    """Generate follow-up response based on GPT analysis"""
    response = VoiceResponse()
    
    if gpt_response.get('is_final'):
        # Final qualification decision
        qualification_result = gpt_response.get('qualification_result', 'unknown')
        summary = gpt_response.get('summary', '')
        
        if qualification_result == 'qualified':
            message = "Bahut achha! Aap qualify ho gaye hain. Hamara team aapko contact karega. Thank you!"
        else:
            message = "Thank you for your time. Hamara team aapko future mein contact kar sakta hai. Goodbye!"
        
        response.say(message, voice='Polly.Aditi', language='hi-IN')
        response.hangup()
        
        # Update Zoho CRM
        if qualification_result == 'qualified':
            crm.mark_lead_qualified(lead_id, summary, str(conversation_states[lead_id]['conversation_history']))
        else:
            crm.mark_lead_disqualified(gpt_response.get('reason', 'No specific reason'), 
                                     str(conversation_states[lead_id]['conversation_history']))
        
        logger.log_call_end(lead_id, qualification_result)
        
    else:
        # Continue conversation with next question
        next_question = gpt_response.get('next_question', 'Kya aap mujhe aur detail de sakte hain?')
        
        response.say(next_question, voice='Polly.Aditi', language='hi-IN')
        
        # Gather next response
        gather = response.gather(
            input='speech',
            language='hi-IN',
            speech_timeout='auto',
            action=f'/twilio/gather?lead_id={lead_id}',
            method='POST'
        )
        
        gather.say("Aap kuch bol sakte hain?", voice='Polly.Aditi', language='hi-IN')
        
        # Fallback
        response.say("Thank you for your time. Goodbye!", voice='Polly.Aditi', language='hi-IN')
        response.hangup()
    
    return response

def _generate_error_response(error_message):
    """Generate error response"""
    response = VoiceResponse()
    response.say(f"Sorry, {error_message}. Please try again later.", voice='Polly.Aditi', language='hi-IN')
    response.hangup()
    return response

def _process_final_qualification(lead_id):
    """Process final qualification if not already done"""
    try:
        if lead_id in conversation_states:
            state = conversation_states[lead_id]
            
            # If conversation didn't reach final qualification, process it now
            if state.get('current_step') != 'completed':
                final_response = gpt_agent.process_final_qualification(lead_id, state)
                
                if final_response.get('is_final'):
                    qualification_result = final_response.get('qualification_result', 'unknown')
                    summary = final_response.get('summary', '')
                    
                    if qualification_result == 'qualified':
                        crm.mark_lead_qualified(lead_id, summary, str(state['conversation_history']))
                    else:
                        crm.mark_lead_disqualified(final_response.get('reason', 'No specific reason'), 
                                                 str(state['conversation_history']))
                    
                    logger.log_call_end(lead_id, qualification_result)
                    
                    # Clean up conversation state
                    del conversation_states[lead_id]
        
    except Exception as e:
        logger.error(f"Error processing final qualification for Lead {lead_id}: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)




