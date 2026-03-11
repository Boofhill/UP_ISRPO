from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import User, Client, Master


def login_view(request):
    if request.method == 'POST':
        login_input = request.POST.get('login')
        password = request.POST.get('password')

        try:
            user = User.objects.get(login=login_input)
            if user.check_password(password):
                # Сохраняем в сессии
                request.session['user_id'] = user.user_id
                request.session['user_type'] = user.type
                request.session['user_name'] = user.fio
                messages.success(request, f'Добро пожаловать, {user.fio}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Неверный пароль')
        except User.DoesNotExist:
            messages.error(request, 'Пользователь не найден')

    return render(request, 'accounts/login.html')


def logout_view(request):
    request.session.flush()
    messages.success(request, 'Вы вышли из системы')
    return redirect('login')


def register_view(request):
    if request.method == 'POST':
        fio = request.POST.get('fio')
        phone = request.POST.get('phone')
        login_input = request.POST.get('login')
        password = request.POST.get('password')
        user_type = request.POST.get('type', 'client')

        if User.objects.filter(login=login_input).exists():
            messages.error(request, 'Логин уже занят')
            return render(request, 'accounts/register.html')

        # Создаем пользователя через менеджер
        user = User.objects.create_user(
            login=login_input,
            password=password,
            fio=fio,
            phone=phone,
            type=user_type
        )

        # Создаем запись в соответствующей таблице
        if user_type == 'client':
            Client.objects.create(user=user)
        elif user_type == 'master':
            Master.objects.create(user=user)

        messages.success(request, 'Регистрация успешна! Войдите в систему.')
        return redirect('login')

    return render(request, 'accounts/register.html')


@login_required
def profile_view(request):
    user_id = request.session.get('user_id')
    user = User.objects.get(user_id=user_id)
    return render(request, 'accounts/profile.html', {'user': user})