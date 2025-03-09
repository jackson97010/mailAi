import ollama
import json
import os
from tools.mail_fetcher import MailFetcher
from tools.mail_classifier import MailClassifier
from tools.mail_summarizer import MailSummarizer

class AIMailAgent:
    def __init__(self, model_name="deepseek-r1:8b"):
        self.fetcher = MailFetcher()
        self.classifier = MailClassifier(model_name)
        self.summarizer = MailSummarizer(model_name)
        self.model = model_name
        self.classified_cache_file = 'classified_emails.json'

    def save_classified_emails(self, emails):
        """Save classified emails to JSON file"""
        try:
            # Convert datetime objects to string for JSON serialization
            serializable_emails = []
            for email_data in emails:
                email_copy = email_data.copy()
                if isinstance(email_copy.get('date'), str):
                    email_copy['date'] = email_copy['date']
                elif hasattr(email_copy.get('date'), 'isoformat'):
                    email_copy['date'] = email_copy['date'].isoformat()
                serializable_emails.append(email_copy)

            with open(self.classified_cache_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_emails, f, indent=2, ensure_ascii=False)
            print(f"\nSaved {len(emails)} classified emails to {self.classified_cache_file}")
        except Exception as e:
            print(f"Error saving classified emails to JSON: {e}")

    def load_classified_emails(self):
        """Load classified emails from JSON cache"""
        try:
            if os.path.exists(self.classified_cache_file):
                with open(self.classified_cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading classified emails: {e}")
        return None

    def process_recent_emails(self, hours=24, use_cache=True):
        """Process and summarize recent emails"""
        print(f"\nFetching emails from the last {hours} hours...")
        emails = self.fetcher.get_emails(time_range_hours=hours, use_cache=use_cache)
        
        # Try to load classified emails from cache
        classified_emails = self.load_classified_emails() if use_cache else None
        
        if not classified_emails:
            print(f"\nClassifying {len(emails)} emails...")
            for email in emails:
                classification = self.classifier.classify_email(email)
                email.update(classification)
            self.save_classified_emails(emails)
        else:
            print("\nUsing cached classifications...")
            emails = classified_emails
        
        print("\nGenerating summary...")
        summary = self.summarizer.summarize_time_period(emails, hours)
        
        return summary

    def get_important_emails(self, hours=24, use_cache=True):
        """Get important emails that need attention"""
        print(f"\nChecking for important emails in the last {hours} hours...")
        
        # Try to load classified emails from cache first
        classified_emails = self.load_classified_emails() if use_cache else None
        
        if not classified_emails:
            emails = self.fetcher.get_emails(time_range_hours=hours, use_cache=use_cache)
            classified_emails = []
            for email in emails:
                classification = self.classifier.classify_email(email)
                email.update(classification)
                classified_emails.append(email)
            self.save_classified_emails(classified_emails)
        
        # Filter important emails
        important_emails = []
        for email in classified_emails:
            if email.get('importance_score', 0) > 0.7 or email.get('requires_action', False):
                if not email.get('summary'):
                    email['summary'] = self.summarizer.summarize_email(email)
                important_emails.append(email)
        
        return important_emails

    def analyze_email(self, email_data):
        """Analyze a single email in detail"""
        prompt = f"""
        Provide a detailed analysis of this email:

        Subject: {email_data['subject']}
        From: {email_data['sender']}
        Content: {email_data['body'][:2000]}

        Please analyze and provide:
        1. Key points and main message
        2. Required actions or next steps
        3. Deadlines or important dates
        4. Suggested response (if needed)
        5. Calendar-related items
        6. Priority level and urgency
        """

        try:
            response = ollama.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}]
            )
            return response['message']['content'].strip()
        except Exception as e:
            print(f"Analysis error: {e}")
            return f"Error analyzing email: {email_data['subject']}"

    def generate_daily_digest(self, hours=24, use_cache=True):
        """Generate a daily digest markdown file of all emails"""
        print(f"\nGenerating daily digest for the last {hours} hours...")
        
        # Try to load classified emails from cache first
        classified_emails = self.load_classified_emails() if use_cache else None
        
        if not classified_emails:
            emails = self.fetcher.get_emails(time_range_hours=hours, use_cache=use_cache)
            classified_emails = []
            print(f"\nClassifying {len(emails)} emails...")
            for email in emails:
                classification = self.classifier.classify_email(email)
                email.update(classification)
                if not email.get('summary'):
                    email['summary'] = self.summarizer.summarize_email(email)
                classified_emails.append(email)
            self.save_classified_emails(classified_emails)
        
        # Generate and save markdown digest
        print("\nGenerating markdown digest...")
        digest = self.summarizer.generate_daily_digest_markdown(classified_emails, hours)
        return digest

def main():
    agent = AIMailAgent("deepseek-r1:8b")
    
    # Generate daily digest
    print("\nGenerating daily email digest...")
    digest = agent.generate_daily_digest(hours=24, use_cache=True)
    print("\nDaily Digest Generated!")
    
    # Process recent emails
    print("\nProcessing recent emails...")
    summary = agent.process_recent_emails(hours=24, use_cache=True)
    print("\nEmail Summary:")
    print(summary)
    
    # Get important emails
    print("\nFetching important emails...")
    important = agent.get_important_emails(hours=24, use_cache=True)
    print("\nImportant Emails:")
    for email in important:
        print(f"\nSubject: {email['subject']}")
        print(f"From: {email['sender']}")
        print(f"Summary: {email['summary']}")
        print(f"Action Required: {email['requires_action']}")
        print(f"Priority Level: {email['priority_level']}")
        print(f"Category: {email['category']}")
        if email.get('deadline'):
            print(f"Deadline: {email['deadline']}")
        print("-" * 50)

if __name__ == "__main__":
    main() 