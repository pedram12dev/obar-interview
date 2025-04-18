import random
from rest_framework.views import APIView
from .models import User, OtpCode, UserLoginAttemp
from django.contrib.auth import authenticate
from .serializers import PhoneNumberSerializer, UserCompleteSerializer
from rest_framework import status
from rest_framework.response import Response
from utils import send_otp_code,get_ip,is_blocked


class PhoneEnterAPIView(APIView):
    def post(self,request):
        ser_data = PhoneNumberSerializer(data=request.data)
        ser_data.is_valid(raise_exception=True)
        phone_number = ser_data.validated_data['phone_number']
        request.session['user_phone_number'] = {
            'phone_number':ser_data.validated_data['phone_number'],
        } # save user phone number in session for login with password or register with otp.
        ip = get_ip(request)
        if User.objects.filter(phone_number=phone_number).exists():
            return Response({'message': 'Phone number exists.You can login with password'}, status=status.HTTP_200_OK)
        else:
            if is_blocked(ip=ip, phone_number=phone_number):
                return Response({'message': 'Your ip blocked,try after 1 hour'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
            random_code = random.randint(100000,999999)
            OtpCode.objects.create(phone_number=phone_number,code=random_code)
            send_otp_code(phone_number,random_code)
            return Response({
                'message': 'phone number does not exists.Otp code sent successfully,you can register with otp code',
                }, status=status.HTTP_200_OK)
            

class LoginWithPasswordAPIView(APIView):
    def post(self,request):
        get_phone_number = request.session['user_phone_number']['phone_number']
        password = request.data.get('password')
        ip = get_ip(request)
        if is_blocked(ip=ip, phone_number=get_phone_number):
            return Response({'message': 'Your ip blocked,try after 1 hour again.'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        user = authenticate(request, phone_number=get_phone_number, password=password)
        if user is not None:
            UserLoginAttemp.objects.create(ip_address=ip, phone_number=get_phone_number, success=True)          
            del request.session['user_phone_number'] # delete phone number from session after login 
            return Response({'message': 'Login successful'}, status=status.HTTP_200_OK)
        else:
            UserLoginAttemp.objects.create(ip_address=ip, phone_number=get_phone_number, success=False)
            return Response({'message': 'Invalid password, try again...'}, status=status.HTTP_401_UNAUTHORIZED)
    

class OtpCodeAPIView(APIView):
    def post(self,request):
        get_phone_number = request.session['user_phone_number']['phone_number']
        otp_code = request.data.get('code')
        ip = get_ip(request)
        if is_blocked(ip=ip, phone_number=get_phone_number):
            return Response({'message': 'Your ip blocked,try after 1 hour again.'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        try:
            otp_code_obj = OtpCode.objects.get(phone_number=get_phone_number, code=otp_code)
            if otp_code_obj.is_expired():
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
