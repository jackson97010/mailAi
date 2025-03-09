import ollama
import json
from datetime import datetime
import os

class MailSummarizer:
    def __init__(self, model_name="deepseek-r1:8b"):
        self.model = model_name
        self.digest_folder = "mail_digests"
        if not os.path.exists(self.digest_folder):
            os.makedirs(self.digest_folder)

    def summarize_email(self, email_data):
        """Summarize a single email using Ollama"""
        prompt = f"""
        Summarize this email concisely:

        Subject: {email_data['subject']}
        From: {email_data['sender']}
        Content: {email_data['body'][:2000]}

        Provide a brief summary that captures:
        1. Main points
        2. Any required actions
        3. Key dates or deadlines (if any)
        4. Important details
        """

        try:
            response = ollama.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}]
            )
            return response['message']['content'].strip()
        except Exception as e:
            print(f"Summarization error: {e}")
            return f"Error summarizing email: {email_data['subject']}"

    def summarize_time_period(self, emails, hours=24):
        """Summarize emails from the past N hours"""
        if not emails:
            return "No emails to summarize."

        email_summaries = []
        for email in emails:
            summary = self.summarize_email(email)
            email_summaries.append({
                'subject': email['subject'],
                'sender': email['sender'],
                'summary': summary,
                'category': email.get('category', 'Uncategorized'),
                'importance': email.get('importance_score', 0.5),
                'requires_action': email.get('requires_action', False)
            })

        # Create overall summary
        prompt = f"""
        Create a comprehensive summary report for the last {hours} hours of emails:

        Email Data:
        {json.dumps(email_summaries, indent=2)}

        Provide a structured summary including:
        1. Total number of emails
        2. Key highlights and important messages
        3. Action items required
        4. Breakdown by category
        5. Time-sensitive items
        """

        try:
            response = ollama.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}]
            )
            return response['message']['content'].strip()
        except Exception as e:
            print(f"Period summarization error: {e}")
            return f"Error creating period summary for the last {hours} hours"

    async def _stream_ollama(self, prompt):
        """Stream response from Ollama"""
        full_response = ""
        async for part in ollama.chat(
            model=self.model,
            messages=[{'role': 'user', 'content': prompt}],
            stream=True
        ):
            if 'content' in part:
                full_response += part['content']
                print(part['content'], end='', flush=True)  # Show streaming output
        return full_response

    def generate_daily_digest_markdown(self, emails, hours=24):
        """Generate a markdown file with a summary of all emails"""
        if not emails:
            return "No emails to summarize."

        # Sort emails by category and importance
        emails_by_category = {}
        for email in emails:
            category = email.get('category', 'Uncategorized')
            if category not in emails_by_category:
                emails_by_category[category] = []
            emails_by_category[category].append(email)

        # Create markdown content
        now = datetime.now()
        markdown_content = f"""# Email Digest for {now.strftime('%Y-%m-%d')}

## Overview
- Total Emails: {len(emails)}
- Time Period: Last {hours} hours
- Categories Found: {', '.join(emails_by_category.keys())}

## Important Highlights
"""
        # Add high priority and action required emails
        important_emails = [e for e in emails if e.get('importance_score', 0) > 0.7 or e.get('requires_action', False)]
        if important_emails:
            markdown_content += "\n### Priority Items\n"
            for email in important_emails:
                markdown_content += f"""
- **{email['subject']}**
  - From: {email['sender']}
  - Priority: {email.get('priority_level', 'Not specified')}
  - Action Required: {email.get('requires_action', False)}
  - Summary: {email.get('summary', 'No summary available')}
"""

        # Add category-wise breakdown
        markdown_content += "\n## Category Breakdown\n"
        for category, category_emails in emails_by_category.items():
            markdown_content += f"\n### {category} ({len(category_emails)} emails)\n"
            for email in category_emails:
                markdown_content += f"""
- **{email['subject']}**
  - From: {email['sender']}
  - Priority: {email.get('priority_level', 'Not specified')}
  - Summary: {email.get('summary', 'No summary available')}
"""

        # Add action items section
        action_items = [e for e in emails if e.get('requires_action', False)]
        if action_items:
            markdown_content += "\n## Action Items\n"
            for email in action_items:
                markdown_content += f"""
- [ ] **{email['subject']}** from {email['sender']}
  - Priority: {email.get('priority_level', 'Not specified')}
  - Action: {email.get('suggested_action', 'Review required')}
  - Deadline: {email.get('deadline', 'Not specified')}
"""

        # Save the markdown file
        filename = f"mail_digest_{now.strftime('%Y%m%d_%H%M%S')}.md"
        filepath = os.path.join(self.digest_folder, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        print(f"\nDaily digest saved to: {filepath}")
        return markdown_content 