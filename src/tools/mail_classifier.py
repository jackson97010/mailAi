import ollama
import json
import asyncio

class MailClassifier:
    def __init__(self, model_name="deepseek-r1:8b"):
        self.model = model_name

    def classify_email(self, email_data):
        """Classify an email and determine its importance and required actions"""
        prompt = f"""
        Analyze this email and provide classification details in JSON format:

        Subject: {email_data['subject']}
        From: {email_data['sender']}
        Content: {email_data['body'][:2000]}

        Provide a JSON response with the following structure:
        {{
            "category": "one of [Work, Personal, Finance, Shopping, Social, News, Spam]",
            "importance_score": "float between 0 and 1",
            "requires_action": "boolean",
            "priority_level": "one of [Low, Medium, High, Urgent]",
            "suggested_action": "string or null if no action needed",
            "deadline": "date string or null if no deadline"
        }}
        """

        try:
            response = ollama.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}]
            )
            
            # Extract JSON from response
            response_text = response['message']['content'].strip()
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0]
            else:
                json_str = response_text
            
            classification = json.loads(json_str)
            return classification
        except Exception as e:
            print(f"Classification error: {e}")
            return {
                "category": "Uncategorized",
                "importance_score": 0.5,
                "requires_action": False,
                "priority_level": "Low",
                "suggested_action": None,
                "deadline": None
            }

    async def _get_ollama_response(self, prompt):
        """Get response from Ollama"""
        full_response = ""
        async for part in ollama.chat(
            model=self.model,
            messages=[{'role': 'user', 'content': prompt}],
            stream=True
        ):
            if 'content' in part:
                full_response += part['content']
        return full_response 