from users.models import ConsumerUser
from django.utils.timezone import now


class ConsumerUserBackend(object):
    def authenticate(self, username=None, password=None):
        try:
            user = ConsumerUser.objects.get(phone=username)
        except ConsumerUser.DoesNotExist:
            pass
        else:
            if user.check_password(password):
                user.last_login = now()
                user.save()
                return user
        return None

    def get_user(self, user_id):
        try:
            return ConsumerUser.objects.get(pk=user_id)
        except ConsumerUser.DoesNotExist:
            return None