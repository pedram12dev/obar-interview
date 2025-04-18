from django.urls import path
from . import views


app_name = 'accounts'
urlpatterns=[
    path('enter-phone/',views.PhoneEnterAPIView.as_view(),name='enter-phone'),
    path('login-with-password/',views.LoginWithPasswordAPIView.as_view(),name='login-with-password'),
    path('check-otp-code/',views.OtpCodeAPIView.as_view(),name='check-otp-code'),
    path('user-register/',views.UserRegisterAPIView.as_view(),name='user-register'),
]