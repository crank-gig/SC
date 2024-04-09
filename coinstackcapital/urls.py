# urls.py

from django.urls import path
from . import views

app_name = "coinstackcapital"
urlpatterns = [
    path('hello-world/', views.hello_world, name='hello_world'),
    path('signup/', views.signup, name='signup'),
    path('authenticate-email/', views.authenticate_email, name='authenticate_email'),
    path('signin/', views.signin, name='signin'),
    path('client-detail/', views.client_detail, name='client_detail'),
    # Add other URL patterns as needed
]
