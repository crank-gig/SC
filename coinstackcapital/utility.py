import json, secrets
from .models import MyUser,UserExistError,EmailMisc, RequestLog, Client, Account
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
import random

#For uuid generation
import uuid
import secrets
from django.contrib.auth import get_user_model
from string import Template

from user_agent import generate_user_agent
from .util.postmark_mailer import PostmarkEmailSender
from django.conf import settings

from django.utils import timezone #Fetches the current datetime
from datetime import timedelta
from django.core.signing import TimestampSigner
signer = TimestampSigner()

#Import for JWT session management
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

#validity of a sesion
_max_age=timedelta(seconds=60)

debug_state=settings.DEBUG

def signUserUp(request,email,username,password,first_name,last_name,country):
    try:
        MyUser.objects.fetch_user_by_email(email)
    except MyUser.DoesNotExist: #OK
        try:
            new_user=MyUser.objects.create_user(email=email, username=username, password=password)
            new_user.country_of_origin=country
            new_user.first_name=first_name
            new_user.last_name=last_name
            new_user.save()

            # Create client object
            Client.objects.create(
                user=new_user, 
                account_holder_digits=generate_holder_digits()
            )

            #Create an account object
            create_holder_account(new_user)

            #Log request
            log_request(request,new_user,"Account created","Approved")

            #Send verification email

            #Send email to admin address

            #Make a fresh token
            refresh = RefreshToken.for_user(new_user)
            
            #Send response
            response=Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                "message": "Account Created"
            },status=200)
            return response
        #Forbidden
        except UserExistError:
            response = JsonResponse({"message": f'The email address {email} exists.'})
            response.status_code=403
            return response
    #Forbidden
    else:
        response = JsonResponse({"message": f'The email address {email} exists.'})
        response.status_code=403
        return response


def signUserIn(email, password):

    try:
        user=MyUser.objects.fetch_user_by_email(email)
        case = MyUser.objects.authenticate(email, password)

        #Bad Request
        if case == False:
            response = JsonResponse({"message": "Please input a correct password."})
            response.status_code=400
            return response
        #Succesful
        else:
            #Make the user active
            user.is_active=True
            user.save()

            #Fetch a new section token
            refresh = RefreshToken.for_user(user)
            
            response=Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                "message": "Successfully logged in"
            },status=200)
            return response

    #Not Found
    except MyUser.DoesNotExist:
        response = JsonResponse({"message": "Email address or password is incorrect."})
        response.status_code=404
        return response


def fetch_client_detail(user):
    # Assuming user is an instance of MyUser model
    # Call the get_all_accounts method
    accounts_queryset = user.get_all_accounts()

    # Format the accounts queryset to an array of dictionaries (JSON format in Python terms)
    accounts_details = [
        {
            'account_name': account.account_name,
            'total_balance': account.total_balance,
            'total_credit': account.total_credit,
            'total_equity_worth': account.total_equity_worth,
            'total_deposits': account.total_deposits,
            'total_withdrawals': account.total_withdrawals
        }
        for account in accounts_queryset
    ]

    # Call the get_all_logs method
    logs_details = user.get_all_logs()  # This method already returns in the desired format

    # Combine both accounts and logs details into a single object
    client_details = {
        'accounts': accounts_details,
        'logs': logs_details,
        'full_name': {
            'first_name': user.first_name,
            'last_name': user.last_name,
        }
    }

    return client_details


def send_verification_email_code(request,email_address):

    new_code = generate_random_code_five_digits()
    
    while(EmailMisc.check_email_code_exists(new_code)):
        new_code = generate_random_code_five_digits()

    #fetch details of operating system and browser and return a string version of the email template to be sent
    operating_system, browser_name = get_user_agent(request)
    input_path = '../email_templates/verify_email.html'  # Replace with the actual input file path
    copied_content = copy_file_content(input_path)

    if 'Error' in copied_content:
        print(f"Error occurred: {copied_content}")
        #substitute parameters into the template  
    else:               
        email_string = substituted_string(
            copied_content,
            {
                "verification_code":new_code,
                "operating_system": operating_system,
                "browser_name": browser_name
            }
        )
        server_token = "142e2f7a-b707-4273-9a19-b241274ad377"
        from_address="geek@snooze.com.ng"
        subject="Drop email verification code"

        status,note=PostmarkEmailSender(
            server_token=server_token,
            from_address=from_address,
            to_address=email_address,
            subject=subject,
            html_body=email_string
        )
        

        #500 Internal Server Error
        if status==None:
            #Means email sending failed
            if debug_state: 
                print(note)
            response = {"reason": "An error occured while trying to process your request. Please try again in a moment"}
            response.status_code=500
            return response
            #return an error note
        else:
            #store the email address, code, reason of email-verification and the current 
            #datetime in the modeland respond telling the user to check their emails
            # Create a new instance of EmailMisc
            new_email_misc = EmailMisc()

            # Set attributes
            new_email_misc.email_address = email_address
            new_email_misc.email_code = "your_email_code"
            new_email_misc.email_code_time = timezone.now()
            new_email_misc.reason = "email-verification"

            # Save the object
            new_email_misc.save()

            response = {"reason": "An email with a verification code has been sent to the provide email address. Retrieve it to continue the registration process"}
            response.status_code=200
            return response


def create_holder_account(user):
    # Retrieve the Client object associated with the user
    try:
        client = Client.objects.get(user=user)
    except Client.DoesNotExist:
        # Handle the case where Client object doesn't exist for the user
        return None

    # Fetch the account holder digits
    account_holder_digits = client.account_holder_digits

    # Count the number of Account objects the user has
    num_accounts = user.account_set.count()

    # Add 1 to the number of accounts and format it as a 3-digit string with leading zeros
    account_number = str(num_accounts + 1).zfill(3)

    # Concatenate the account holder digits with the formatted account number
    new_account_name = f'W_{account_holder_digits}_{account_number}'

    # Create a new Account object
    new_account = Account.objects.create(
        user=user,
        account_name=new_account_name,
        total_balance='0',
        total_credit='0',
        total_equity_worth='0',
        total_deposits='0',
        total_withdrawals='0'
    )

    return new_account


def generate_holder_digits():
    while True:
        # Generate a 7-digit random number
        random_number = ''.join(random.sample('0123456789', 7))
        # Check if any Client has the same account_holder_digits
        if not Client.objects.filter(account_holder_digits=random_number).exists():
            return random_number


def log_request(request, user, label, status):

    # Create a new RequestLog entry
    RequestLog.objects.create(
        user=user,
        status=status,
        label=label,
        user_agent=request.META.get('HTTP_USER_AGENT', None),  # Set to None if not found
        referrer=request.META.get('HTTP_REFERER', None),  # Set to None if not found
        http_method=request.method,
        request_url=request.build_absolute_uri(),
        request_header=str(request.headers),
        client_ip_address=request.META.get('REMOTE_ADDR', None),  # Set to None if not found
        geolocation_data={},  # You can populate this based on your requirements
        date_time=timezone.now(),  # Assuming you have the datetime field in your RequestLog model
    )

def delete_account(user):
    #Delete account object
    account=Account.objects.get(user=user)
    account.delete()
    #Delete request log
    request_log=RequestLog.objects.get(user=user)
    request_log.delete()
    #Delete client object
    client=Client.objects.get(user=user)
    client.delete()
    #Delete user object
    user.delete()

def check_for_session_id(request):
    try:
        #try getting the session id
        session_id=request.session["sessid"]
    except:
        #means there's no id; move user to specified url
        return None
    else:
        #id exists so check the id for expiry
        try:
            signer.unsign(session_id, max_age = _max_age)
        except:
            #user session id expired; send to the requested url
            return False
        else:
            #user not yet expired; redirect them to the homepage or dashboard
            return True


def generate_random_code_five_digits():
    return ''.join(random.choices('0123456789', k=5))


def copy_file_content(input_file_path):
    try:
        with open(input_file_path, 'r') as input_file: 
            # Read content from the input file
            file_content = input_file.read()

            return file_content
    except Exception as e:
        # Handle any exceptions (e.g., file not found, permission issues)
        return f"Error: {str(e)}"


def get_user_agent(request):
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    # Extract operating system and browser information from the user agent
    operating_system = generate_user_agent(user_agent)['os']['name']
    browser_name = generate_user_agent(user_agent)['browser']['name']
    return operating_system, browser_name


def substituted_string(context,map):
    #This function takes a string called the context, and inputs a value from the dictionary
    #called the map using a key
    string_template=Template(context)
    response=string_template.substitute(map)
    return response
    

def sameSiteChecker(request):
    allowed_referer = 'http://localhost'#Replace with the allowed domain
    referer = request.META.get('HTTP_REFERER', '')

    origin = request.headers.get('Origin')

    if origin in settings.CORS_ALLOWED_ORIGINS and allowed_referer in referer:
        return True
    else:
        return False

#Test request
simulated_request = {
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36',
    'referrer': 'https://www.example.com',
    'http_method': 'GET',
    'request_url': 'https://www.example.com/some-path',
    'request_header': {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'Host': 'www.example.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36',
        # Add other headers as needed
    },
    'client_ip_address': '192.168.1.1',
    'geolocation_data': {},  # Populate based on your requirements
    'date_time': timezone.now(),
}


if __name__ == "__main__":
   signUserUp(None,"crankgig@gmail.com","crank", "crank")

#function to query polygon.io's
"""
    request url format: https://api.polygon.io/v2/reference/news?published_utc=2024-04-01&limit=100&apiKey=pvCYhLodQ0ZKMZ8_dtA6s7lt0pkwuguF

    response format
    {
    "results": [
        {
            "id": "-HHEMjoS1ozn2Ld7MJtIBlDcPqxpudJ5HrtpxWArAfM",
            "publisher": {
                "name": "GlobeNewswire Inc.",
                "homepage_url": "https://www.globenewswire.com",
                "logo_url": "https://s3.polygon.io/public/assets/news/logos/globenewswire.svg",
                "favicon_url": "https://s3.polygon.io/public/assets/news/favicons/globenewswire.ico"
            },
            "title": "Aura Reports Updated Mineral Reserves and Mineral Resources",
            "author": "Aura Minerals Inc",
            "published_utc": "2024-04-01T23:43:00Z",
            "article_url": "https://www.globenewswire.com/news-release/2024/04/01/2855583/0/en/Aura-Reports-Updated-Mineral-Reserves-and-Mineral-Resources.html",
            "tickers": [
                "ORA"
            ],
            "amp_url": "https://www.globenewswire.com/news-release/2024/04/01/2855583/0/en/Aura-Reports-Updated-Mineral-Reserves-and-Mineral-Resources.html",
            "image_url": "https://ml.globenewswire.com/Resource/Download/616f120d-3c78-4c9f-ae3c-6310752513cf",
            "description": "Aura Reports Updated Mineral Reserves and Mineral Resources",
            "keywords": [
                "Technical Analysis"
            ]
        },
        {
            "id": "mKYKyNIRZDYycINZc5jh-4E2NDlbyoB2rnvT6xPUMCs",
            "publisher": {
                "name": "GlobeNewswire Inc.",
                "homepage_url": "https://www.globenewswire.com",
                "logo_url": "https://s3.polygon.io/public/assets/news/logos/globenewswire.svg",
                "favicon_url": "https://s3.polygon.io/public/assets/news/favicons/globenewswire.ico"
            },
            "title": "Kayne Anderson Energy Infrastructure Fund Provides Unaudited Balance Sheet Information and Announces Its Net Asset Value and Asset Coverage Ratios At March 31, 2024",
            "author": "Kayne Anderson Energy Infrastructure Fund, Inc.",
            "published_utc": "2024-04-01T23:30:00Z",
            "article_url": "https://www.globenewswire.com/news-release/2024/04/01/2855581/0/en/Kayne-Anderson-Energy-Infrastructure-Fund-Provides-Unaudited-Balance-Sheet-Information-and-Announces-Its-Net-Asset-Value-and-Asset-Coverage-Ratios-At-March-31-2024.html",
            "tickers": [
                "KYN"
            ],
            "amp_url": "https://www.globenewswire.com/news-release/2024/04/01/2855581/0/en/Kayne-Anderson-Energy-Infrastructure-Fund-Provides-Unaudited-Balance-Sheet-Information-and-Announces-Its-Net-Asset-Value-and-Asset-Coverage-Ratios-At-March-31-2024.html",
            "image_url": "https://ml.globenewswire.com/Resource/Download/73ea9f82-d965-4d81-9eb7-ba36b417c4cf",
            "description": "HOUSTON, April  01, 2024  (GLOBE NEWSWIRE) -- Kayne Anderson Energy Infrastructure Fund, Inc. (the “Company”) (NYSE: KYN) today provided a summary unaudited statement of assets and liabilities and announced its net asset value and asset coverage ratios under the Investment Company Act of 1940 (the “1940 Act”) as of March 31, 2024.",
            "keywords": [
                "Company Announcement"
            ]
        },
        {
            "id": "KpivVVsBX0vjR66eAgPv6-w0JQ3H6D56Fzlj5Dzqv6w",
            "publisher": {
                "name": "GlobeNewswire Inc.",
                "homepage_url": "https://www.globenewswire.com",
                "logo_url": "https://s3.polygon.io/public/assets/news/logos/globenewswire.svg",
                "favicon_url": "https://s3.polygon.io/public/assets/news/favicons/globenewswire.ico"
            },
            "title": "Canoo Inc. Announces Fourth Quarter and Fiscal Year 2023 Financial Results",
            "author": "CANOO",
            "published_utc": "2024-04-01T22:37:00Z",
            "article_url": "https://www.globenewswire.com/news-release/2024/04/01/2855573/0/en/Canoo-Inc-Announces-Fourth-Quarter-and-Fiscal-Year-2023-Financial-Results.html",
            "tickers": [
                "GOEV"
            ],
            "amp_url": "https://www.globenewswire.com/news-release/2024/04/01/2855573/0/en/Canoo-Inc-Announces-Fourth-Quarter-and-Fiscal-Year-2023-Financial-Results.html",
            "image_url": "https://ml.globenewswire.com/Resource/Download/d110e5ef-60fa-414e-bb19-f94590e96dc6",
            "description": "JUSTIN, Texas, April  01, 2024  (GLOBE NEWSWIRE) -- Canoo Inc. (Nasdaq: GOEV), a high-tech advanced mobility company, today announced its financial results for the fourth quarter and fiscal year 2023.",
            "keywords": [
                "Earnings Releases and Operating Results"
            ]
        },
    ]
    }

"""