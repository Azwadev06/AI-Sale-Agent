# AI Voice Sales Agent 🎯

An intelligent, AI-powered voice sales agent that automatically qualifies leads using Hindi voice calls. This system integrates Zoho CRM, Twilio Voice, and OpenAI GPT-4 to create a fully automated sales qualification pipeline.

## ✨ Features

- **🤖 AI-Powered**: Uses GPT-4 for dynamic, contextual sales questions
- **🇮🇳 Hindi Voice**: Speaks in Hindi using Amazon Polly voices via Twilio
- **📞 Automated Calling**: Places calls to leads automatically using Twilio
- **📊 CRM Integration**: Fetches and updates leads in Zoho CRM
- **🧠 Smart Qualification**: Determines lead qualification using BANT criteria
- **📝 Conversation Logging**: Records all conversations for analysis
- **🔄 Production Ready**: Modular, maintainable, and scalable architecture

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Zoho CRM      │    │   Twilio Voice  │    │   OpenAI GPT-4  │
│   (Leads)       │◄──►│   (Calls)       │◄──►│   (AI Agent)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       ▲                       ▲
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Main Agent    │
                    │ (Orchestrator)  │
                    └─────────────────┘
```

## 📁 Project Structure

```
.
├── main.py                      # Main orchestrator script
├── test_connections.py          # Connection testing utility
├── requirements.txt             # Python dependencies
├── env.example                  # Environment variables template
├── README.md                    # This file
├── zoho/                        # Zoho CRM integration
│   ├── __init__.py
│   ├── auth.py                  # OAuth2 authentication
│   └── crm.py                   # CRM operations
├── twilio/                      # Twilio integration
│   ├── __init__.py
│   ├── call.py                  # Call management
│   └── webhook.py               # Flask webhook app
├── gpt/                         # OpenAI integration
│   ├── __init__.py
│   └── agent.py                 # GPT-4 agent logic
└── utils/                       # Utilities
    ├── __init__.py
    └── logger.py                # Logging system
```

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.8+
- Zoho CRM account with API access
- Twilio account with voice capabilities
- OpenAI API key (GPT-4 access)
- Public webhook endpoint (ngrok for local development)

### 2. Installation

```bash
# Clone the repository
git clone <repository-url>
cd ai-voice-sales-agent

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp env.example .env
```

### 3. Configuration

Edit `.env` file with your credentials:

```bash
# Zoho CRM
ZOHO_CLIENT_ID=your_client_id
ZOHO_CLIENT_SECRET=your_client_secret
ZOHO_REFRESH_TOKEN=your_refresh_token
ZOHO_DC=com  # Data center (com, eu, in, au, jp)

# Twilio
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=your_twilio_number

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Flask
FLASK_SECRET_KEY=your_secret_key
WEBHOOK_BASE_URL=https://your-domain.com  # For production
```

### 4. Test Connections

```bash
# Test all external service connections
python test_connections.py
```

### 5. Start the System

```bash
# Start webhook server (in one terminal)
python twilio/webhook.py

# In another terminal, test the system
python main.py --status

# Run automated campaign
python main.py --campaign 5
```

## 🔧 Setup Guide

### Zoho CRM Setup

1. **Create Zoho App**:
   - Go to [Zoho Developer Console](https://api-console.zoho.com/)
   - Create a new client
   - Set redirect URI to `https://your-domain.com/oauth/callback`
   - Note down Client ID and Client Secret

2. **Get Refresh Token**:
   - Visit: `https://accounts.zoho.com/oauth/v2/auth?scope=ZohoCRM.modules.ALL&client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=YOUR_REDIRECT_URI`
   - Authorize and get the authorization code
   - Exchange code for refresh token

3. **Set Data Center**:
   - Use appropriate data center (com, eu, in, au, jp)
   - Update `ZOHO_DC` in `.env`

### Twilio Setup

1. **Create Twilio Account**:
   - Sign up at [Twilio](https://www.twilio.com/)
   - Get Account SID and Auth Token

2. **Get Phone Number**:
   - Purchase a phone number with voice capabilities
   - Note down the phone number

3. **Configure Webhooks**:
   - Set webhook URLs in Twilio console
   - Use ngrok for local development

### OpenAI Setup

1. **Get API Key**:
   - Visit [OpenAI Platform](https://platform.openai.com/)
   - Create API key
   - Ensure GPT-4 access

## 📱 Usage

### Command Line Interface

```bash
# Show system status
python main.py --status

# Test connections
python main.py --test

# Test fetching leads
python main.py --fetch-leads

# Test updating a lead
python main.py --update-lead LEAD_ID

# Call a specific lead
python main.py --call-lead LEAD_ID

# Run automated campaign
python main.py --campaign 10 --delay 5
```

### Webhook Endpoints

The Flask webhook server provides these endpoints:

- `POST /twilio/voice/<lead_id>` - Handle incoming calls
- `POST /twilio/gather` - Process speech input
- `POST /twilio/status` - Call status updates
- `POST /twilio/recording` - Recording status updates

### Conversation Flow

1. **Lead Selection**: System fetches next available lead from Zoho CRM
2. **Call Initiation**: Twilio places call to lead's phone number
3. **Greeting**: AI greets lead in Hindi and asks first question
4. **Dynamic Questions**: GPT-4 generates contextual follow-up questions
5. **Qualification**: After 3-4 exchanges, AI determines qualification
6. **CRM Update**: Result is written back to Zoho CRM
7. **Next Lead**: System moves to next lead

## 🎯 Sales Qualification Logic

The AI agent uses **BANT criteria** for qualification:

- **Budget**: Does the lead have budget for the solution?
- **Authority**: Can they make purchasing decisions?
- **Need**: Do they have a genuine need for the solution?
- **Timeline**: Do they need a solution soon?

### Qualification Questions (Hindi)

The system asks questions like:
- "Aapka business kya hai aur kitne saal se chal raha hai?"
- "Aapke company mein kitne employees hain?"
- "Aapka annual revenue kya hai?"
- "Aapko kya challenges face kar rahe hain?"
- "Aap kab tak solution chahte hain?"

## 🔍 Testing

### Connection Tests

```bash
# Test all services
python test_connections.py

# Test individual components
python main.py --test
```

### Lead Operations

```bash
# Test lead fetching
python main.py --fetch-leads

# Test lead updates
python main.py --update-lead LEAD_ID
```

### Call Testing

```bash
# Test calling specific lead
python main.py --call-lead LEAD_ID

# Run small campaign
python main.py --campaign 3
```

## 📊 Monitoring & Logging

### Log Files

- Logs are stored in `logs/` directory
- Rotating log files (10MB max, 5 backups)
- Console and file logging

### Log Levels

- `INFO`: General operations
- `DEBUG`: Detailed debugging info
- `ERROR`: Error conditions
- `WARNING`: Warning conditions

### Key Metrics

- Call success/failure rates
- Lead qualification rates
- GPT response times
- CRM operation success rates

## 🚀 Production Deployment

### Webhook Server

```bash
# Using Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 twilio.webhook:app

# Using systemd service
sudo systemctl enable ai-voice-agent
sudo systemctl start ai-voice-agent
```

### Environment Variables

- Set `WEBHOOK_BASE_URL` to your production domain
- Use strong `FLASK_SECRET_KEY`
- Set appropriate `LOG_LEVEL`

### Security Considerations

- Use HTTPS for webhooks
- Implement rate limiting
- Monitor API usage
- Secure environment variables

## 🐛 Troubleshooting

### Common Issues

1. **Zoho Authentication Failed**:
   - Check refresh token validity
   - Verify data center setting
   - Ensure proper OAuth scopes

2. **Twilio Call Fails**:
   - Verify phone number format
   - Check webhook URL accessibility
   - Ensure sufficient Twilio credits

3. **GPT-4 Errors**:
   - Verify API key validity
   - Check API usage limits
   - Ensure GPT-4 access

4. **Webhook Not Receiving Calls**:
   - Check webhook server status
   - Verify webhook URLs in Twilio
   - Check firewall/network settings

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with verbose output
python main.py --status
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Add tests
5. Submit pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the logs for error details

## 🔮 Future Enhancements

- [ ] Multi-language support
- [ ] Advanced analytics dashboard
- [ ] Integration with more CRMs
- [ ] Machine learning for better qualification
- [ ] Call recording analysis
- [ ] A/B testing for questions
- [ ] Performance optimization
- [ ] Mobile app for monitoring

---

**Built with ❤️ using Python, Flask, Twilio, OpenAI, and Zoho CRM**

