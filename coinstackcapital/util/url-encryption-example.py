import hashlib
from string import Template
import hmac
import urllib.parse

# Secret key shared between you and the merchant
secret_key = "your_secret_key"

# Parameters to be included in the URL
params = {
    "amount": 300,
    "currency": "eth",
    "api-key": "6511064641:AAGASzXbqsvAKaO_0mp-SKHw5IGW2wuH1UI",
    "user-id": "6511064641",
}

# Template for the URL
url_template = Template("https://your-api-endpoint.com/pay?${query}")

# Format the URL with the parameters
url = url_template.substitute(query=urllib.parse.urlencode(params))

# Generate the HMAC signature
message = url.encode("utf-8")
signature = hmac.new(secret_key.encode("utf-8"), message, hashlib.sha256).hexdigest()

# Append the HMAC signature to the URL
secure_url = f"{url}&signature={signature}"

print("Original URL:", url)
print("Secure URL:", secure_url)
