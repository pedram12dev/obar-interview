from django.utils import timezone
from accounts.models import UserLoginAttemp


def send_otp_code(phone_number , code):
    """
    Send OTP code to the user's phone number.
     - args:
            phone_number (str): The user's phone number.
            code (str): The OTP code to send.
     - returns:
            None

    this function fill with sms service.
    """
    pass


def get_ip(request):
    """
    Get the user's IP address from the request.
     - args:
            request (HttpRequest): The HTTP request object.
     - returns:
            str: The user's IP address.
    """
    
    return request.META.get('REMOTE_ADDR')


def is_blocked(ip,phone_number):
    """
    Check if the user is blocked based on their IP address and phone number.
     - args:
            ip (str): The user's IP address.
            phone_number (str): The user's phone number.
     - returns:
            bool: True if the user is blocked, False otherwise.
    """
    
    try:
        block_time = timezone.now() - timezone.timedelta(hours=1)
        blocked_user = UserLoginAttemp.objects.filter(ip_address=ip, phone_number=phone_number,success=False, created_at__gte=block_time).count()
        if blocked_user >= 3:
            return True
        else:
            return False
    except UserLoginAttemp.DoesNotExist:
        return False