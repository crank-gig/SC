import requests
import json
import asyncio

#post mark class for drop
class PostmarkEmailSender:
    def __init__(self, server_token, from_address, to_address, subject, html_body, message_stream="outbound"):
        self.url = "https://api.postmarkapp.com/email"
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Postmark-Server-Token": server_token
        }
        self.data = {
            "From": from_address,
            "To": to_address,
            "Subject": subject,
            "HtmlBody": html_body,
            "MessageStream": message_stream
        }

    async def send_async(self):
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: requests.post(self.url, headers=self.headers, data=json.dumps(self.data)))
            return response.status_code, response.text
        except requests.exceptions.RequestException as e:
            # Handle exception (e.g., connection error)
            return None, str(e)

    def send(self):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.send_async())
    
if __name__ == "__main__":
    # Replace 'YOUR_SERVER_TOKEN' with your actual Postmark server token
    server_token = "142e2f7a-b707-4273-9a19-b241274ad377"
    
    # Instantiate the class with email details
    email_sender = PostmarkEmailSender(
        server_token,
        from_address="geek@snooze.com.ng",
        to_address="geek@snooze.com.ng",
        subject="Hello from Postmark",
        html_body="<strong>Hello</strong> dear Postmark user."
    )

    # Send the email and get the response
    status_code, response_text = email_sender.send()

    # Print the status code and response text
    print(f"Status Code: {status_code}")
    print(f"Response Text: {response_text}")
