from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


class Role(models.Model):
    """Гибкие роли с правами"""
    name = models.CharField(max_length=50, unique=True, verbose_name="Название роли")
    can_create_tickets = models.BooleanField(default=False, verbose_name="Создание заявок")
    can_view_all_tickets = models.BooleanField(default=False, verbose_name="Просмотр всех заявок")
    can_change_ticket_status = models.BooleanField(default=False, verbose_name="Изменение статуса")
    can_assign_master = models.BooleanField(default=False, verbose_name="Назначение мастера")
    can_manage_users = models.BooleanField(default=False, verbose_name="Управление пользователями")
    can_manage_roles = models.BooleanField(default=False, verbose_name="Управление ролями")
    can_view_stats = models.BooleanField(default=False, verbose_name="Просмотр статистики")

    class Meta:
        db_table = 'roles'
        verbose_name = 'Роль'
        verbose_name_plural = 'Роли'

    def __str__(self):
        return self.name


class UserManager(BaseUserManager):
    def create_user(self, login, password=None, **extra_fields):
        if not login:
            raise ValueError('Логин должен быть указан')
        user = self.model(login=login, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, login, password=None, **extra_fields):
        extra_fields.setdefault('type', 'admin')
        # Получаем или создаём роль админа
        admin_role, _ = Role.objects.get_or_create(
            name='admin',
            defaults={
                'can_create_tickets': True,
                'can_view_all_tickets': True,
                'can_change_ticket_status': True,
                'can_assign_master': True,
                'can_manage_users': True,
                'can_manage_roles': True,
                'can_view_stats': True,
            }
        )
        extra_fields.setdefault('role', admin_role)
        return self.create_user(login, password, **extra_fields)


class User(AbstractBaseUser):
    USER_TYPES = (
        ('client', 'Клиент'),
        ('master', 'Мастер'),
        ('admin', 'Администратор'),
    )

    user_id = models.AutoField(primary_key=True)
    fio = models.CharField(max_length=100, verbose_name="ФИО")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    login = models.CharField(max_length=50, unique=True, verbose_name="Логин")
    password = models.CharField(max_length=255, verbose_name="Пароль")
    type = models.CharField(max_length=20, choices=USER_TYPES, default='client', verbose_name="Тип пользователя")
    role = models.ForeignKey(
        Role, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Роль", db_column='roleID'
    )

    last_login = None
    is_active = True

    USERNAME_FIELD = 'login'
    REQUIRED_FIELDS = ['fio', 'phone']

    objects = UserManager()

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def has_perm(self, permission_name):
        """Проверяет наличие конкретного права у роли пользователя"""
        if not self.role:
            return False
        return getattr(self.role, permission_name, False)

    def __str__(self):
        return f"{self.fio} ({self.get_type_display()})"

    class Meta:
        db_table = 'users'
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class Client(models.Model):
    client_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='userID')

    class Meta:
        db_table = 'clients'
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'


class Master(models.Model):
    master_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='userID')

    class Meta:
        db_table = 'masters'
        verbose_name = 'Мастер'
        verbose_name_plural = 'Мастера'