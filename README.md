# AI Mail Agent

An intelligent email management system that uses AI to process, classify, and summarize your emails.

## Features

- Email fetching from IMAP servers (Gmail supported by default)
- AI-powered email classification and importance scoring
- Detailed email analysis and summarization
- Action item detection and deadline tracking
- Periodic email summaries

## Prerequisites

- Python 3.8 or higher
- Ollama installed and running locally
- Email account with IMAP access enabled
- For Gmail: App-specific password or 2FA enabled

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with your email settings:
```env
EMAIL=your.email@gmail.com
EMAIL_PASSWORD=your-app-specific-password
IMAP_SERVER=imap.gmail.com
IMAP_PORT=993
```

## Usage

Basic usage example:

```python
import asyncio
from src.ai_mail_agent import AIMailAgent

async def main():
    # Initialize the agent
    agent = AIMailAgent("llama2")
    
    # Get a summary of recent emails
    summary = await agent.process_recent_emails(hours=24)
    print(summary)
    
    # Get important emails that need attention
    important = await agent.get_important_emails(hours=24)
    for email in important:
        print(f"\nSubject: {email['subject']}")
        print(f"From: {email['sender']}")
        print(f"Summary: {email['summary']}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Security Notes

- Never commit your `.env` file or expose your email credentials
- Use app-specific passwords when possible
- Review the permissions granted to the application

## License

MIT License 