import os
import openai
import json
from datetime import datetime
from utils.logger import logger

class GPTAgent:
    """AI agent using GPT-4 for dynamic sales qualification"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("Missing OpenAI API key")
        
        openai.api_key = self.api_key
        self.model = "gpt-4"
        
        # Sales qualification questions in Hindi
        self.qualification_questions = [
            "Aapka business kya hai aur kitne saal se chal raha hai?",
            "Aapke company mein kitne employees hain?",
            "Aapka annual revenue kya hai?",
            "Aap currently kya use kar rahe hain?",
            "Aapko kya challenges face kar rahe hain?",
            "Aap kab tak solution chahte hain?",
            "Aapke budget ke baare mein kya sochte hain?",
            "Aap decision lene mein kaun involve hain?"
        ]
        
        # System prompt for sales qualification
        self.system_prompt = """You are an AI sales agent conducting lead qualification calls in Hindi. 
        Your goal is to determine if a lead is qualified for your product/service.
        
        Guidelines:
        1. Always respond in Hindi (Hinglish is acceptable)
        2. Ask relevant follow-up questions based on user responses
        3. Determine qualification based on BANT criteria (Budget, Authority, Need, Timeline)
        4. Be conversational and professional
        5. After 3-4 exchanges, make a qualification decision
        
        Qualification criteria:
        - QUALIFIED: Lead has budget, authority, need, and timeline
        - DISQUALIFIED: Lead lacks one or more BANT criteria
        
        Respond in JSON format:
        {
            "is_final": true/false,
            "next_question": "question in Hindi",
            "qualification_result": "qualified/disqualified/unknown",
            "reason": "reason for qualification decision",
            "summary": "brief summary of conversation"
        }"""
    
    def process_user_response(self, lead_id, user_response, conversation_state):
        """Process user response and determine next action"""
        try:
            # Add user response to conversation history
            conversation_state['conversation_history'].append({
                'speaker': 'user',
                'message': user_response,
                'timestamp': datetime.now().isoformat()
            })
            
            # Check if we have enough information for qualification
            if len(conversation_state['conversation_history']) >= 6:  # 3 exchanges
                return self._make_qualification_decision(lead_id, conversation_state)
            
            # Generate next question
            next_question = self._generate_next_question(user_response, conversation_state)
            
            # Add AI response to conversation history
            conversation_state['conversation_history'].append({
                'speaker': 'ai',
                'message': next_question,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.log_gpt_interaction(lead_id, "Generated question", next_question)
            
            return {
                "is_final": False,
                "next_question": next_question,
                "qualification_result": "unknown",
                "reason": "",
                "summary": ""
            }
            
        except Exception as e:
            logger.error(f"Error processing user response for Lead {lead_id}: {str(e)}")
            return {
                "is_final": False,
                "next_question": "Kya aap mujhe aur detail de sakte hain?",
                "qualification_result": "unknown",
                "reason": "",
                "summary": ""
            }
    
    def _generate_next_question(self, user_response, conversation_state):
        """Generate next question based on user response"""
        try:
            # Create conversation context
            context = self._build_conversation_context(conversation_state)
            
            # Use GPT to generate contextual question
            prompt = f"""Based on this conversation context, generate the next sales qualification question in Hindi:

Context: {context}

User's last response: {user_response}

Generate a natural follow-up question in Hindi that helps qualify this lead. The question should be relevant to what the user just said.

Question in Hindi:"""

            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful sales assistant. Respond only with the question in Hindi, nothing else."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.7
            )
            
            next_question = response.choices[0].message.content.strip()
            
            # Fallback to predefined questions if GPT fails
            if not next_question or len(next_question) < 10:
                used_questions = [msg['message'] for msg in conversation_state['conversation_history'] if msg['speaker'] == 'ai']
                available_questions = [q for q in self.qualification_questions if q not in used_questions]
                
                if available_questions:
                    next_question = available_questions[0]
                else:
                    next_question = "Aapke business ke baare mein aur kya bata sakte hain?"
            
            return next_question
            
        except Exception as e:
            logger.error(f"Error generating next question: {str(e)}")
            return "Aapke business ke baare mein aur kya bata sakte hain?"
    
    def _make_qualification_decision(self, lead_id, conversation_state):
        """Make final qualification decision using GPT"""
        try:
            context = self._build_conversation_context(conversation_state)
            
            prompt = f"""Based on this sales conversation, determine if the lead is QUALIFIED or DISQUALIFIED.

Conversation context: {context}

Analyze the BANT criteria:
- Budget: Does the lead have budget?
- Authority: Can they make decisions?
- Need: Do they have a genuine need?
- Timeline: Do they need a solution soon?

Respond in this exact JSON format:
{{
    "is_final": true,
    "next_question": "",
    "qualification_result": "qualified" or "disqualified",
    "reason": "specific reason for decision",
    "summary": "brief summary of key points"
}}"""

            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.3
            )
            
            try:
                result = json.loads(response.choices[0].message.content.strip())
                logger.log_gpt_interaction(lead_id, "Qualification decision", str(result))
                return result
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON response from GPT for Lead {lead_id}")
                return self._fallback_qualification(conversation_state)
                
        except Exception as e:
            logger.error(f"Error making qualification decision for Lead {lead_id}: {str(e)}")
            return self._fallback_qualification(conversation_state)
    
    def _fallback_qualification(self, conversation_state):
        """Fallback qualification logic if GPT fails"""
        # Simple rule-based qualification
        user_responses = [msg['message'] for msg in conversation_state['conversation_history'] if msg['speaker'] == 'user']
        
        # Check for positive indicators
        positive_indicators = ['yes', 'haan', 'bilkul', 'zaroor', 'interested', 'budget', 'decision', 'need', 'urgent']
        negative_indicators = ['no', 'nahi', 'not interested', 'no budget', 'no need', 'later', 'busy']
        
        positive_count = sum(1 for response in user_responses for indicator in positive_indicators if indicator.lower() in response.lower())
        negative_count = sum(1 for response in user_responses for indicator in negative_indicators if indicator.lower() in response.lower())
        
        if positive_count > negative_count and len(user_responses) >= 3:
            result = "qualified"
            reason = "Positive responses indicate interest and need"
        else:
            result = "disqualified"
            reason = "Insufficient positive indicators or negative responses"
        
        return {
            "is_final": True,
            "next_question": "",
            "qualification_result": result,
            "reason": reason,
            "summary": f"Fallback qualification: {reason}. Responses analyzed: {len(user_responses)}"
        }
    
    def _build_conversation_context(self, conversation_state):
        """Build conversation context for GPT"""
        context_parts = []
        
        for i, message in enumerate(conversation_state['conversation_history']):
            speaker = "AI" if message['speaker'] == 'ai' else "User"
            context_parts.append(f"{speaker}: {message['message']}")
        
        return "\n".join(context_parts)
    
    def process_final_qualification(self, lead_id, conversation_state):
        """Process final qualification if conversation ended abruptly"""
        try:
            if len(conversation_state['conversation_history']) >= 2:
                return self._make_qualification_decision(lead_id, conversation_state)
            else:
                # Not enough conversation for qualification
                return {
                    "is_final": True,
                    "next_question": "",
                    "qualification_result": "disqualified",
                    "reason": "Insufficient conversation for qualification",
                    "summary": "Call ended too early to qualify lead"
                }
        except Exception as e:
            logger.error(f"Error in final qualification for Lead {lead_id}: {str(e)}")
            return self._fallback_qualification(conversation_state)
    
    def test_connection(self):
        """Test OpenAI API connection"""
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            logger.info("OpenAI API connection test successful")
            return True
        except Exception as e:
            logger.error(f"OpenAI API connection test failed: {str(e)}")
            return False








