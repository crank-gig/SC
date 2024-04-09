import os
import re
import resend
resend.api_key = "re_ZiJG94e2_3Y8QW4MuBrpGbHyDdQcdYWVX"

regex = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+') 







def is_valid_email(email):  
    if re.fullmatch(regex, email):  
     return email  
    else:  
     return None 

html_email = """
    <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Email Verification</title>
</head>
<body style="font-family: Arial, sans-serif; margin: 0; padding: 0;">

    <div style="background-color: #f4f4f4; padding: 20px;">
        <h2 style="color: #333;">Verify Your Email Address</h2>
        <p style="color: #333;">Dear User,</p>
        <p style="color: #333;">Thank you for signing up. Please click the button below to verify your email address.</p>
        <a href="https://example.com/verify-email" style="display: inline-block; background-color: #007bff; color: #fff; text-decoration: none; padding: 10px 20px; border-radius: 5px;">Verify Email Address</a>
        <p style="color: #333;">If you didn't create an account, you can safely ignore this email.</p>
        <p style="color: #333;">Thanks,<br>Your Company</p>
    </div>

</body>
</html>

"""

def Mailer(from_email,subject,to_email):    
    params = {
                    "from": from_email,
                    "to": [to_email],
                    "subject": subject,
                    "html": html_email,
                    }
    return resend.Emails.send(params)
    
if __name__ == "__main__":
   Mailer("crankgig@gmail.com","Verification Email", "noapiere@gmail.com")
