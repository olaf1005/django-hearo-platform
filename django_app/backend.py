from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class EmailBackend(ModelBackend):
    def authenticate(self, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        if username:
            try:
                user = UserModel.objects.get(username=username)
            except UserModel.DoesNotExist:
                return None
            else:
                if user.check_password(password):
                    return user
        elif "email" in kwargs:
            try:
                user = UserModel.objects.get(email=kwargs["email"])
            except UserModel.DoesNotExist:
                return None
            else:
                if user.check_password(password):
                    return user
        return None
