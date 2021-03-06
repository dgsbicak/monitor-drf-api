from django.db import models
from django.utils.translation import gettext_lazy as _
from datetime import date, datetime, timedelta
from django.utils import timezone

from django.contrib import auth
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)
from django.core.validators import EmailValidator
from django.core.mail import send_mail
from django.apps import apps



class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, username, email, password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        if not username:
            raise ValueError('The given username must be set')
        email = self.normalize_email(email)
        # Lookup the real model class from the global app registry so this
        # manager method can be used in migrations. This is fine because
        # managers are by definition working on the real model.
        GlobalUserModel = apps.get_model(self.model._meta.app_label, self.model._meta.object_name)
        username = GlobalUserModel.normalize_username(username)
        user = self.model(username=username, email=email, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(username, email, password, **extra_fields)

    def with_perm(self, perm, is_active=True, include_superusers=True, backend=None, obj=None):
        if backend is None:
            backends = auth._get_backends(return_tuples=True)
            if len(backends) == 1:
                backend, _ = backends[0]
            else:
                raise ValueError(
                    'You have multiple authentication backends configured and '
                    'therefore must provide the `backend` argument.'
                )
        elif not isinstance(backend, str):
            raise TypeError(
                'backend must be a dotted import path string (got %r).'
                % backend
            )
        else:
            backend = auth.load_backend(backend)
        if hasattr(backend, 'with_perm'):
            return backend.with_perm(
                perm,
                is_active=is_active,
                include_superusers=include_superusers,
                obj=obj,
            )
        return self.none()


class AbstractUser(AbstractBaseUser, PermissionsMixin):
    """
    An abstract base class implementing a fully featured User model with
    admin-compliant permissions.
    """
    username_validator = UnicodeUsernameValidator()
    email_validator = EmailValidator()

    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[username_validator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    first_name = models.CharField(_('first name'), max_length=50, blank=True)
    last_name = models.CharField(_('last name'), max_length=50, blank=True)
    email = models.EmailField(
        _('email address'),
        blank=True,
        unique=True,
        help_text=_('Letters, digits and @/./-/_ only.'),
        validators=[email_validator],
        error_messages={
            'unique':_("An account with that email already exists."),
        },
    )
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    objects = UserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['first_name','last_name','email']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        #abstract = True

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Send an email to this user."""
        send_mail(subject, message, from_email, [self.email], **kwargs)


class User(AbstractUser):
    """
    Users within the Django authentication system are represented by this
    model.

    Username and password are required. Other fields are optional.
    """
    class Meta(AbstractUser.Meta):
        swappable = 'AUTH_USER_MODEL'


class Machine(models.Model):
    class MachineType(models.TextChoices):
        ANY="ANY", _("Any"),
        DESKTOP = "DT", _("Desktop"),
        CLOUDSERVER = "CS", _('Cloud Server')
        SINGLE_BOARD_COMPUTERS = "SBC", _('Single Board')
    created = models.DateTimeField(auto_now_add=True)
    machinename = models.CharField(primary_key=True, max_length=100, blank=False, unique=True)
    machineid = models.IntegerField(null=False, unique=True)
    hasgpu = models.BooleanField(default=False)
    machinetype = models.CharField(
        max_length=5,
        choices=MachineType.choices,
        default=MachineType.ANY)
    
    class Meta:
        ordering = ('-created',)

    def is_tangible(self):
        return self.machinetype in {
                MachineType.DESKTOP, 
                MachineType.SINGLE_BOARD_COMPUTERS
            }
    def has_gpu(self):
        return self.hasgpu is True
    
    def __str__(self):
        return "{}".format(self.machinename)


class MachineInfo(models.Model):

    class TodaysObjects(models.Manager):
        def get_queryset(self):
            return super().get_queryset().filter(
                created__gte=(timezone.now() - timedelta(days=1))
            )

    machine = models.ForeignKey(Machine,to_field="machinename",on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    cpuutil = models.FloatField()
    cpumem = models.FloatField()
    gpuutil = models.FloatField(null=True)
    gpumem = models.FloatField(null=True)
    diskspaceleft = models.FloatField(null=True)
    disk_r = models.FloatField(null=True)
    disk_w = models.FloatField(null=True)
    network_r = models.FloatField(null=True)
    network_t = models.FloatField(null=True)
    internet_access = models.BooleanField(null=True)
    running = models.BooleanField()
    objects = models.Manager() # default manager
    todaysobjects = TodaysObjects() # custom manager

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return "Machine-{}, is running: {}".format(self.machine, self.running)

    def is_recent(self):
        return self.created > (timezone.now() - timedelta(days=1))
