from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model

from .utility import signUserUp, send_verification_email_code, signUserIn,sameSiteChecker
from .utility import fetch_client_detail

#For uuid generation
import uuid

from django.utils import timezone #Fetches the current datetime
from .models import EmailMisc, MyUser, RateLimit

from datetime import timedelta
from django.core.signing import TimestampSigner
signer = TimestampSigner()
_max_age=timedelta(seconds=60)

debug_state=settings.DEBUG
unauth_quota=30 #request per minute
auth_quota=60 #request per minute

@api_view(['GET'])
def hello_world(request):
    if request.user.is_authenticated:
        print("authenticated")
        return JsonResponse({'message': f'Hello, {request.user.username}!'})
    else:
        print("not authenticated")
        return JsonResponse({'message': 'Not authenticated'})

@api_view(['POST']) #A post should be used
def signup(request):
    #first checks for the ip or domain

    # Check if the origin is in the allowed list
    if sameSiteChecker(request):
        if request.method == 'POST':
            username = request.data.get('email').split("@")[0]
            email_address = request.data.get('email')
            password = request.data.get('password')
            first_name = request.data.get('first_name')
            last_name = request.data.get('last_name')
            country = request.data.get('country')
            #check if email address is verified
            #                
            return signUserUp(
                request=request,
                email=email_address,
                username=username,
                password=password,
                first_name =first_name,
                last_name=last_name,
                country=country
            )
    else:
        return JsonResponse({'message': 'Unauthorized access'}, status=403)
    
@api_view(['POST']) #A post should be used
def authenticate_email(request):
    #first checks for the ip or domain

    # Check if the origin is in the allowed list
    if sameSiteChecker(request):
        if request.method == 'POST':
            email_address = request.data.get('email')

            #success
            try:
                MyUser.objects.fetch_user_by_email(email_address)
                return JsonResponse({'message': f'{email_address} exists.'}, status=200)
            #Not Found
            except MyUser.DoesNotExist:
                return JsonResponse({'message': f'{email_address} does not exist.'}, status=404)
                pass
    #Unauthorized access
    else:
        return JsonResponse({'message': 'Unauthorized access'}, status=403)
    
@api_view(['POST']) #A post should be used
def signin(request):
    #first checks for the ip or domain

    # Check if the origin is in the allowed list
    if sameSiteChecker(request):
        if request.method == 'POST':
            email_address = request.data.get('email')
            password = request.data.get('password')

            return signUserIn(email=email_address,password=password)
    #Unauthorized access
    else:
        return JsonResponse({'message': 'Unauthorized access'}, status=403)
    
@api_view(['GET']) #A get should be used
def client_detail(request):
    #first checks for the ip or domain

    # Check if the origin is in the allowed list
    if sameSiteChecker(request):
        if request.method == 'GET':
            if request.user.is_authenticated:
                client_detail=fetch_client_detail(request.user)
                return JsonResponse({'message':client_detail}, status=200)
            else:
                return JsonResponse({'message': 'Session expired.'}, status=403)
    #Unauthorized access
    else:
        return JsonResponse({'message': 'Unauthorized access'}, status=403)
    
@csrf_exempt
def refresh_token(request):
    if request.method == 'POST':
        refresh_token = request.POST.get('refresh_token')
        if refresh_token:
            try:
                refresh_token = RefreshToken(refresh_token)
                access_token = str(refresh_token.access_token)
                return JsonResponse({'access_token': access_token}, status=200)
            except Exception as e:
                return JsonResponse({'error': 'Invalid refresh token'}, status=400)
        else:
            return JsonResponse({'error': 'Refresh token not provided'}, status=400)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

@api_view(['GET','POST']) #A post should be used
def sendEmailVerificationRequest(request):

    if sameSiteChecker(request):
        if request.method=='POST':
            email_address=request.POST.get('email')
            email_misc_object = EmailMisc.get_by_address(email_address)

            if email_misc_object:
                object_time=email_misc_object.email_code_time
                object_code=email_misc_object.email_code
                reason=email_misc_object.reason

                if object_time > timezone.now() and object_code and reason == "email-verification": 
                    #means the time is valid and they should check their emails for the code sent
                    response = {"reason": "Please check your email address for the code sent"}
                    response.status_code=200
                    return response
                elif object_time < timezone.now() and object_code and reason == "email-verification":
                    #Means the time has expired resend a new code and update the time.
                    #create a new code and check if it exists
                    response = send_verification_email_code(request,email_address)            
                    return response
            else:
                #No object found send an email and record the details
                response = send_verification_email_code(request,email_address)            
                return response
    else:
        return JsonResponse({'error': 'Unauthorized access'}, status=403)
    
@api_view(['GET','POST']) #A post should be used
def checkEmailVerificationRequest(request):

    if sameSiteChecker(request):
        if request.method=='POST':
            code=request.POST.get('code')
            email_misc_object = EmailMisc.check_email_code_exists(code)

            if email_misc_object:
                object_time=email_misc_object.email_code_time
                reason=email_misc_object.reason

                #200 Success
                if timezone.now() < object_time + timezone.timedelta(hours=1) and reason == "email-verification": 
                    #means the time is valid and you should change the reason to verified
                    email_misc_object.email_code = ""
                    email_misc_object.email_code_time = None
                    email_misc_object.reason = "verified"
                    email_misc_object.save()

                    response = {"reason": "Your email address has been verified. You can continue with you registration"}
                    response.status_code=200
                    return response
                #400 Bad Request
                elif timezone.now() >= object_time + timezone.timedelta(hours=1) and reason == "email-verification":
                    #Means the time has expired, but the code is valid 
                    #So we delete the entry from the database and inform them to request a new code.
                    #create a new code and check if it exists
                    response = {"reason": "The code you submitted is expired. Please request for a new one."}
                    response.status_code=400
                    return response
            #404 Not Found
            else:
                #No object found send an email and record the details
                response = {"reason": "The code you submitted is invalid. Please try again."}
                response.status_code=404
                return response
    else:
        return JsonResponse({'error': 'Unauthorized access'}, status=403)
   


    