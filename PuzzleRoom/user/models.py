#C:\Users\beka\OneDrive\Desktop\Year4DjangoMajor-Project\DjangoProject\PuzzleRoom\user\models.py
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
# Removed: from rooms.models import PuzzleRoom

class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None, is_guest=False, **extra_fields):
        if not username:
            raise ValueError('The Username field must be set')
        
        if not is_guest and not email:
            raise ValueError('The Email field must be set for non-guest users')

        email = self.normalize_email(email) if email else None
        user = self.model(email=email, username=username, is_guest=is_guest, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, username, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, null=True, blank=True)
    username = models.CharField(max_length=30, unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    password = models.CharField(max_length=128)
    join_date = models.DateTimeField(default=timezone.now)
    puzzle_room = models.ForeignKey('sliding_puzzle.PuzzleRoom', on_delete=models.SET_NULL, null=True, blank=True)
    is_guest = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)  # Add this line
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.username if self.is_guest else self.email
