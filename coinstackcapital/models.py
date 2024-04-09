import datetime
from django.contrib import admin
from django.utils import timezone
import uuid
import secrets

from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
#imported for using a custom user model and manager
rate_quota=30

class UserExistError(Exception):
    pass


#MyUser Model Manager
class MyUserManager(BaseUserManager):
    def create_user(self, email, username, password=None):
        """
        Creates and saves a User with the given email, 
        username and password.
        """
        if not email or not username or not password:
            raise ValueError("Users must have an email, username and password")
        
        try:
            self.fetch_user_by_email(email)
        except MyUser.DoesNotExist:
            #Means email does not exist; create user
            try:
                self.fetch_user_by_username(email)
            except MyUser.DoesNotExist:
                #Means username does not exist; create  user
                user = self.model( 
                    email=email,
                    username=username
                )

                user.set_password(password)
                user.save(using=self._db)
                return user
            else:
                raise UserExistError
        else:
            raise UserExistError
        
    def create_superuser(self, email, username, password=None):
        """
        Creates and saves a superuser with the given email,
        username and password
        """
        user = self.create_user(
            email,
            username,
            password
        )
        user.is_admin = True
        user.save(using=self._db)
        return user

    def fetch_all_users(self):
        return super().get_queryset().all()    
 
    def fetch_user_by_email(self,email):
        return self.get(email=email)

    def fetch_user_by_username(self,username):
        return self.get(username=username)
    
    def authenticate(self, email, password):
        user = self.fetch_user_by_email(email)
        case = user.check_password(password)
        return case

class Auth_Data(models.Model):
    # file will be uploaded to MEDIA-URL/uploads
    # beforehand in the settings.py MEDIA-URL/ has been assigned to MEDIA_ROOT
    id_card = models.FileField(
        upload_to="uploads/", blank=True, verbose_name="ID Card"
    )
    passport = models.FileField(
        upload_to="uploads/", blank=True, verbose_name="Passport"
    )
    drivers_license = models.FileField(
        upload_to="uploads/", blank=True, verbose_name="Driver's License"
    )
    voters_card = models.FileField(
        upload_to="uploads/", blank=True, verbose_name="Voter's Card"
    )
    bank_statement = models.FileField(
        upload_to="uploads/", blank=True, verbose_name="Bank Statement"
    )
    utility_bill = models.FileField(
        upload_to="uploads/", blank=True, verbose_name="Utility Bill"
    )
    #This field maps datetime string of the upload date and time of any of these files to
    #its stringified field name
    log = models.JSONField()


#This model uses the JSONField for all entries
class Security_Settings(models.Model):
    two_factor_auth_preferences = models.JSONField(
        blank=True
    )
    security_questions = models.JSONField(
        blank=True
    )
    email_notif_settings = models.JSONField(
        blank=True
    )
    sms_notif_settings = models.JSONField(
        blank=True
    )


class RateLimit(models.Model):
    ip_address = models.GenericIPAddressField()
    rate_limit_reset = models.DateTimeField()
    rate_limit_remaining = models.PositiveIntegerField()

    def __str__(self):
        return f"RateLimit for {self.ip_address}"
    
    @classmethod
    def handle_rate_limit(cls, ip_address):
        # Try to get the RateLimit object with the given IP address
        rate_limit_obj, created = cls.objects.get_or_create(ip_address=ip_address)

        # Get the current time
        current_time = timezone.now()

        if created or rate_limit_obj.rate_limit_reset <= current_time:
            # Reset the rate limit if it has expired
            rate_limit_obj.rate_limit_reset = current_time + timezone.now(minutes=1)
            rate_limit_obj.rate_limit_remaining = rate_quota-1
        elif rate_limit_obj.rate_limit_reset > current_time and rate_limit_obj.rate_limit_remaining == 0:
            # Deny the request if rate limit is reached
            return False
        else:
            # Decrement the remaining rate limit and save
            rate_limit_obj.rate_limit_remaining -= 1

        # Save the RateLimit object
        rate_limit_obj.save()

        # Request is allowed
        return True


class Referral(models.Model):
    referral_code = models.CharField(
        max_length=50, blank=True
    )
    referral_link = models.CharField(
        max_length=50, blank=True
    )
    rewards = models.CharField(
        max_length=50, blank=True
    )


#Django allows you to override the default user model by providing a 
#value for the AUTH_USER_MODEL setting that references a custom model

#For our application user's primary key, django's default is used 
#On the front end, a hash of it is used or shown
class MyUser(AbstractBaseUser):
    email = models.EmailField(
        verbose_name="email address", max_length=255, unique=True,
    )
    username = models.CharField(
        verbose_name="Username", max_length=255, unique=True, blank=True
    )
    first_name = models.CharField(
        max_length=50, verbose_name="First name", blank=True
    )
    last_name = models.CharField(
        max_length=50, verbose_name="Last name", blank=True
    )
    other_names = models.CharField(
        max_length=100, verbose_name="Other names", blank=True
    )
    date_of_birth = models.DateField(
        verbose_name="Date of Birth", blank=True, null=True
    )
    country_of_origin = models.CharField(
        verbose_name="Country of Origin", blank=True, null=True, max_length= 60
    )
    #The first element in each tuple is the actual value to be set on the model, 
    # and the second element is the human-readable name.
    KYC_STATE = [
        ("Untouched", "Untouched"),
        ("Pending", "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
    ]
    kyc_status= models.CharField(
        max_length=9, choices=KYC_STATE, default="Untouched", blank=True
    )
    ACCOUNT_STATE = [
        ("Active", "Active"),
        ("Suspended", "Suspended"),
        ("Banned", "Banned"),
    ]
    account_status = models.CharField(
        max_length=9, choices=ACCOUNT_STATE, default="Active", blank=True
    )
    auth_data = models.OneToOneField(
        Auth_Data, on_delete=models.CASCADE, blank=True, null=True
    )
    security_setting = models.OneToOneField(
        Security_Settings, on_delete=models.CASCADE, blank=True, null=True
    )
    referral = models.OneToOneField(
        Referral, on_delete=models.CASCADE, blank=True, null=True
    )
    misc = models.JSONField(blank=True,default=dict,null=True)
    #APP specifics

    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = MyUserManager()

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "username"

    #The first request log attached to this user
    def get_first_request_log_details(self):
        if self.logs:
            first_log = self.logs
            return {
                "label": first_log.label,
                "user_agent": first_log.user_agent,
                "referrer": first_log.referrer,
                "http_method": first_log.http_method,
                "request_url": first_log.request_url,
                "request_header": first_log.request_header,
                "client_ip_address": first_log.client_ip_address,
                "geolocation_data": first_log.geolocation_data,
                "date_time": first_log.date_time,
            }
        else:
            return None

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin

    #Fetches all the account object of a user
    def get_all_accounts(self):
        """Query all Account objects associated with the user."""
        return self.account_set.all()

    #get all the associated logs attached to a user
    def get_all_logs(self):
        """
        Fetch all the logs associated with the user and return just the label
        and datetime field of each.
        """
        if self.request_logs:
            return [
                {
                    'label': log.label, 
                    'date_time': log.date_time.strftime('%d/%m/%Y %H:%M'), 
                    'status': log.status
                } for log in self.request_logs.all()]
        else:
            return []

    #For graceful deletion    
    def delete(self, *args, **kwargs):
        # Add custom logic to handle deletion
        # For example, you might want to transfer ownership of accounts
        # or perform other actions before deletion
        super().delete(*args, **kwargs)


class RequestLog(models.Model):
    user = models.ForeignKey(MyUser, related_name='request_logs', on_delete=models.PROTECT, null=True)
    STATUS_STATE = [
        ("Untouched", "Untouched"),
        ("Pending", "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
    ]
    status= models.CharField(
        max_length=9, choices=STATUS_STATE, default="Untouched", blank=True
    )
    label = models.CharField(max_length=255, null=True, blank=True)
    user_agent = models.CharField(max_length=255)
    referrer = models.CharField(max_length=255, null=True, blank=True)
    referrer = models.CharField(max_length=255, null=True, blank=True)
    http_method = models.CharField(max_length=10)
    request_url = models.URLField()
    request_header = models.TextField()
    client_ip_address = models.GenericIPAddressField()
    geolocation_data = models.JSONField(null=True, blank=True)
    date_time = models.DateTimeField(
        blank=True
    )

    def __str__(self):
        return f"RequestLog {self.id}: {self.http_method} {self.request_url}"


class Client(models.Model):
    user = models.OneToOneField(MyUser, on_delete=models.PROTECT)
    account_holder_digits = models.CharField(max_length=7, unique=True)


class Address(models.Model):
    street = models.CharField(
        max_length=50, verbose_name="Street", blank=True
    )
    city = models.CharField(
        max_length=50, verbose_name="City", blank=True
    )
    state_or_province = models.CharField(
        max_length=50, verbose_name="State/Province", blank=True
    )
    county = models.CharField(
        max_length=50, verbose_name="County", blank=True
    )
    postal_or_zip = models.PositiveSmallIntegerField(
        verbose_name="Postal/Zip Code", blank=True
    )
    Country = models.CharField(
        max_length=50, verbose_name="Country", blank=True
    )
    addresse = models.ForeignKey(
        MyUser, on_delete=models.CASCADE
    )


class EmailMisc(models.Model):
    email_address = models.EmailField(blank=True)
    email_code = models.CharField(max_length=255, blank=True)
    email_code_time = models.DateTimeField(blank=True)
    email_link = models.URLField(blank=True)
    email_link_time = models.DateTimeField(blank=True)
    #The first element in each tuple is the actual value to be set on the model, 
    #and the second element is the human-readable name
    REASON_CHOICES = [
        ('email-verification', 'Email Verification'),
        ('password-change', 'Password Change'),
        ('verified', 'verified'),
    ]
    reason = models.CharField(max_length=20, choices=REASON_CHOICES, blank=True)

    def __str__(self):
        return f"{self.email_address} - {self.reason}"

    #method for getting an object instance with email_address
    @classmethod
    def get_by_address(cls, email_address):
        try:
            return cls.objects.get(email_address=email_address)
        except cls.DoesNotExist:
            return None
    #method to check if a code exists in this model
    @classmethod
    def check_email_code_exists(cls, email_code_to_check):
        # Query the database to check if an object with the specified email_code exists
        return cls.objects.filter(email_code=email_code_to_check).exists()
    

class Account(models.Model):
    user = models.ForeignKey(MyUser, on_delete=models.PROTECT, null=True)
    account_name = models.CharField(max_length=100)
    total_balance = models.CharField(max_length=100)
    total_credit = models.CharField(max_length=100)
    total_equity_worth = models.CharField(max_length=100)
    total_deposits = models.CharField(max_length=100)
    total_withdrawals = models.CharField(max_length=100)