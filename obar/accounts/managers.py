from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    """
        1. create user function: 
            - give phone number ,email , full_name , password. 
            - check user enter phone number and email.
            - create user with attr and save user in db.
            - return user 
        2. create super user for admin panel and shell :
            - give phone number ,email , full_name , password. 
            - create user with attr and save user in db.
            - return user 
    """
    def create_user(self , phone_number , email , full_name , password):
        if not phone_number:
            raise ValueError('user must have phone number')
        if not email:
            raise ValueError('user must have email')

        user = self.model(phone_number=phone_number , email=self.normalize_email(email) , full_name=full_name)
        user.set_password(password)
        user.save(using = self._db)
        return user

    def create_superuser(self , phone_number , email , full_name , password):
        user=self.create_user(phone_number=phone_number , email=email , full_name=full_name , password=password)
        user.is_admin=True
        user.save(using=self._db)
        return user