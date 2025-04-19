import random
from rest_framework.views import APIView
from .models import User, OtpCode, UserLoginAttemp
from django.contrib.auth import authenticate
from .serializers import PhoneNumberSerializer, UserCompleteSerializer
from rest_framework import status
from rest_framework.response import Response
from utils import send_otp_code,get_ip,is_blocked


class PhoneEnterAPIView(APIView):
    """
        this view handles the phone number entry for login or registration.
        it checks if the phone number exists in the database and sends an OTP code
        if it does not. It also checks if the IP address is blocked.
        phone number is saved in session for login with password or register with otp or register.
    """
    def post(self,request):
        ser_data = PhoneNumberSerializer(data=request.data) # serialize phone number
        ser_data.is_valid(raise_exception=True) 
        phone_number = ser_data.validated_data['phone_number'] # get phone number from serializer
        request.session['user_phone_number'] = {
            'phone_number':ser_data.validated_data['phone_number'],
        } # save user phone number in session for login with password or register with otp.
        ip = get_ip(request)
        if User.objects.filter(phone_number=phone_number).exists():
            return Response({'message': 'Phone number exists.You can login with password'}, status=status.HTTP_200_OK)
        else:
            if is_blocked(ip=ip, phone_number=phone_number):
                return Response({'message': 'Your ip blocked,try after 1 hour'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
            random_code = random.randint(100000,999999) # generate random 6 digit code
            OtpCode.objects.create(phone_number=phone_number,code=random_code) # create otp code object
            send_otp_code(phone_number,random_code) # send otp code to user phone number
            return Response({
                'message': 'phone number does not exists.Otp code sent successfully,you can register with otp code',
                }, status=status.HTTP_200_OK)
            

class LoginWithPasswordAPIView(APIView):
    """
        this view handles the login with password.
        it checks if the user exists and if the password is correct.
        it also checks if the IP address is blocked.
        if the login is successful, it deletes the phone number from the session.

    """
    def post(self,request):
        get_phone_number = request.session['user_phone_number']['phone_number'] # get phone number from session
        password = request.data.get('password') # get password from request data
        ip = get_ip(request) # get ip address from request
        if is_blocked(ip=ip, phone_number=get_phone_number): # check if ip is blocked
            return Response({'message': 'Your ip blocked,try after 1 hour again.'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        user = authenticate(request, phone_number=get_phone_number, password=password)
        if user is not None:
            # if user is not none create user login attempt object and success true.
            UserLoginAttemp.objects.create(ip_address=ip, phone_number=get_phone_number, success=True)          
            del request.session['user_phone_number'] # delete phone number from session after login 
            return Response({'message': 'Login successful'}, status=status.HTTP_200_OK)
        else:
            # if user is none create user login attempt object and success false.
            UserLoginAttemp.objects.create(ip_address=ip, phone_number=get_phone_number, success=False)
            return Response({'message': 'Invalid password, try again...'}, status=status.HTTP_401_UNAUTHORIZED)
    

class OtpCodeAPIView(APIView):
    """
        this view handles the OTP code verification.
        it checks if the OTP code is valid and not expired.
        if the OTP code is valid, it marks it as verified and deletes it.
        it also checks if the IP address is blocked.
        if the OTP code is expired, it deletes it and returns an error message.
        if the OTP code is invalid, it creates a user login attempt object with success false.
        if the OTP code is valid, it creates a user login attempt object with success true.
        it also deletes the OTP code after verification.
    """
    def post(self,request):
        get_phone_number = request.session['user_phone_number']['phone_number'] # get phone number from session
        otp_code = request.data.get('code') # get otp code from request data
        ip = get_ip(request)
        # check if ip is blocked
        if is_blocked(ip=ip, phone_number=get_phone_number):
            return Response({'message': 'Your ip blocked,try after 1 hour again.'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        try:
            otp_code_obj = OtpCode.objects.get(phone_number=get_phone_number, code=otp_code)
            if otp_code_obj.is_expired(): # check if otp code is expired
                otp_code_obj.delete()
                return Response({'message': 'Otp code expired'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                otp_code_obj.verified = True
                otp_code_obj.save()
                UserLoginAttemp.objects.create(ip_address=ip, phone_number=get_phone_number, success=True)          
                otp_code_obj.delete()
                return Response({'message': 'Otp code verified successfully, now you can register'}, status=status.HTTP_200_OK)
        except OtpCode.DoesNotExist:
            UserLoginAttemp.objects.create(ip_address=ip, phone_number=get_phone_number, success=False)
            return Response({'message': 'Invalid otp code'}, status=status.HTTP_400_BAD_REQUEST)
        

class UserRegisterAPIView(APIView):
    """
        this view handles the user registration.
        create user with phone number, email, full name and password.
        after successful registration, delete the phone number from session.
    """
    def post(self,request):
        get_phone_number = request.session['user_phone_number']['phone_number']
        ser_data = UserCompleteSerializer(data=request.data)
        if ser_data.is_valid():
            user = User.objects.create_user(
                phone_number=get_phone_number,
                email=ser_data.validated_data['email'],
                full_name=ser_data.validated_data['full_name'],
                password=ser_data.validated_data['password']
            )
            user.save()
            del request.session['user_phone_number']
            return Response({'message': 'User registered successfully'}, status=status.HTTP_201_CREATED)
        else:
            return Response(ser_data.errors, status=status.HTTP_400_BAD_REQUEST)
