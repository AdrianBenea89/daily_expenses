import uuid
import os
from datetime import datetime
from django.conf import settings
from django.dispatch import receiver
from django.core.mail import send_mail
from django.db import models
from django.db.models import Sum

from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db.models.signals import post_save


def expense_image_file_path(instance, filename):
    """Generate file path for new expense image."""
    ext = os.path.splitext(filename)[1]
    filename = f'{uuid.uuid4()}{ext}'
    return os.path.join('uploads', 'expense', filename)


def user_images(instance, filename):
    date_time = datetime.now().strftime("%Y_%m_%d,%H:%M:%S")
    saved_file_name = instance.email + "-" + date_time + ".jpg"
    return 'uploads/profile/{0}/{1}'.format(instance.email, saved_file_name)


class UserProfileManager(BaseUserManager):
    """Manager for user profiles"""
    def create_user(self, email, name, region, password=None):
        """Create a new user profile"""
        if not email:
            raise ValueError("User must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, region=region)

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, name, region, password):
        """Create and save new superuser with details"""
        user = self.create_user(email, name, region, password)

        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)

        return user


class UserProfile(AbstractBaseUser, PermissionsMixin):
    """Database model for users in the system"""
    region_choices = (("Europe", "Europe"),
                      ("Asia", "Asia"),
                      ("America", "America"))
    email = models.EmailField(max_length=255,
                              unique=True)
    name = models.CharField(max_length=255)
    region = models.CharField(max_length=50,
                              choices=region_choices,
                              blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)

    last_email_sent_date = models.DateField(null=True, blank=True)
    daily_expenses_limit = models.DecimalField(
        max_digits=5,
        decimal_places=0, default=200)
    image = models.ImageField(upload_to=user_images,
                              default='uploads/profile/default/default.png')

    objects = UserProfileManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'region']

    def get_full_name(self):
        """Retrieve fullname of the user"""
        return self.name

    def get_region(self):
        """Retrieve region of the user"""
        return self.region

    def __str__(self):
        """Return string representation of our user"""
        return self.email


class Category(models.Model):
    """Database model for expenses categories"""
    category_name = models.CharField(max_length=255)
    description = models.CharField(max_length=255,
                                   blank=True)
    created_at = models.DateField(
        auto_now_add=True)
    is_active = models.BooleanField(
        default=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.category_name


class UserDailyExpenses(models.Model):
    """Database model for user expenses"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE)
    expense_name = models.CharField(max_length=255)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE
    )
    price = models.DecimalField(
        max_digits=7,
        decimal_places=2)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)
    image = models.ImageField(null=True, upload_to=expense_image_file_path)

    def __str__(self):
        """Return the model as a string"""
        return self.expense_name


@receiver(post_save, sender=UserDailyExpenses)
def expense_notification(sender, instance, created, **kwargs):
    """Sends an email when reaching the expense limit"""
    qs = sender.objects.filter(user=instance.user)
    last_1_day = qs.filter(created_at=datetime.now()).aggregate(Sum('price'))
    daily_expenses_sum = list(last_1_day.values())[0]
    """User queryset"""
    user_qs = UserProfile.objects.get(email=instance.user)
    user_email_sent = user_qs.last_email_sent_date

    subject = f'Passed the limit with {instance.expense_name}'
    message = f'You just bought ' \
              f'{instance.expense_name} ' \
              f'and you got to the limit per day of ' \
              f'{user_qs.daily_expenses_limit} RON!'
    if daily_expenses_sum >= user_qs.daily_expenses_limit and \
            user_email_sent != instance.created_at:
        send_mail(
            subject, message,
            settings.EMAIL_HOST_USER,
            ['adrian.benea89@gmail.ro', user_qs.email],
            fail_silently=False)
        user_qs.last_email_sent_date = datetime.today()
        user_qs.save()
