import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

class Logger:
    """Centralized logging utility for the AI Voice Sales Agent"""
    
    def __init__(self, name="ai_voice_agent", log_level=None):
        self.logger = logging.getLogger(name)
        
        # Set log level from environment or default to INFO
        if log_level is None:
            log_level = os.getenv('LOG_LEVEL', 'INFO')
        
        level = getattr(logging, log_level.upper(), logging.INFO)
        self.logger.setLevel(level)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup console and file handlers"""
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler with rotation
        logs_dir = "logs"
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
        
        file_handler = RotatingFileHandler(
            f"{logs_dir}/ai_voice_agent.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
    
    def info(self, message):
        """Log info message"""
        self.logger.info(message)
    
    def error(self, message):
        """Log error message"""
        self.logger.error(message)
    
    def warning(self, message):
        """Log warning message"""
        self.logger.warning(message)
    
    def debug(self, message):
        """Log debug message"""
        self.logger.debug(message)
    
    def critical(self, message):
        """Log critical message"""
        self.logger.critical(message)
    
    def log_call_start(self, lead_id, phone_number):
        """Log the start of a call"""
        self.info(f"Starting call to Lead ID: {lead_id}, Phone: {phone_number}")
    
    def log_call_end(self, lead_id, qualification_result):
        """Log the end of a call with result"""
        self.info(f"Call ended for Lead ID: {lead_id}, Result: {qualification_result}")
    
    def log_gpt_interaction(self, lead_id, question, response):
        """Log GPT interactions"""
        self.debug(f"Lead {lead_id}: GPT Q: {question[:100]}... | A: {response[:100]}...")
    
    def log_zoho_operation(self, operation, lead_id, status):
        """Log Zoho CRM operations"""
        self.info(f"Zoho {operation}: Lead {lead_id} - {status}")

# Global logger instance
logger = Logger()








