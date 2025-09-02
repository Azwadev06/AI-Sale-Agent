# AI Voice Sales Agent - Deployment Guide

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Copy `env.example` to `.env` and fill in your credentials:
```bash
cp env.example .env
```

### 3. Run the Application
```bash
python3 main.py
```

## 📋 Required Environment Variables

### Zoho CRM
- `ZOHO_CLIENT_ID` - Your Zoho Client ID
- `ZOHO_CLIENT_SECRET` - Your Zoho Client Secret  
- `ZOHO_REFRESH_TOKEN` - Your Zoho Refresh Token
- `ZOHO_DC` - Data center (com, eu, in, au, jp)

### Twilio
- `TWILIO_ACCOUNT_SID` - Your Twilio Account SID
- `TWILIO_AUTH_TOKEN` - Your Twilio Auth Token
- `TWILIO_PHONE_NUMBER` - Your Twilio Phone Number
- `WEBHOOK_BASE_URL` - Your public webhook URL (e.g., https://your-domain.com)

### OpenAI
- `OPENAI_API_KEY` - Your OpenAI API Key

### Flask
- `FLASK_SECRET_KEY` - Random secret key for Flask sessions

## 🌐 Production Deployment

### For Cloud Deployment (Heroku, AWS, etc.)
1. Set `WEBHOOK_BASE_URL` to your production domain
2. Use a production WSGI server like Gunicorn
3. Set `FLASK_ENV=production`

### For Local Testing
1. Use ngrok or similar tool to expose localhost
2. Set `WEBHOOK_BASE_URL` to your ngrok URL

## 📞 How It Works

1. **Lead Fetching**: Gets leads from Zoho CRM
2. **AI Qualification**: Uses GPT-4 to qualify leads via voice calls
3. **Call Management**: Twilio handles voice calls and webhooks
4. **CRM Updates**: Results are written back to Zoho CRM

## 🔧 Testing

Run the test command to verify all connections:
```bash
python3 main.py --test
```

## 📁 Project Structure

```
├── main.py                 # Main application entry point
├── requirements.txt        # Python dependencies
├── env.example            # Environment variables template
├── gpt/                   # AI agent module
├── twilio_directory/      # Twilio integration
├── zoho/                  # Zoho CRM integration
└── utils/                 # Utility functions
```

## 🆘 Support

For technical support, contact your development team.

