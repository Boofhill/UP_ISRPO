from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import User, Client, Master, Role


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


def profile_view(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, 'Необходимо войти в систему')
        return redirect('login')
    user = User.objects.get(user_id=user_id)
    return render(request, 'accounts/profile.html', {'user': user})


# Управление ролями (только admin)
def role_list(request):
    user_type = request.session.get('user_type')
    if user_type != 'admin':
        messages.error(request, 'Доступ запрещён')
        return redirect('dashboard')

    roles = Role.objects.all()
    return render(request, 'admin/role_list.html', {'roles': roles})


def role_create(request):
    user_type = request.session.get('user_type')
    if user_type != 'admin':
        messages.error(request, 'Доступ запрещён')
        return redirect('dashboard')

    if request.method == 'POST':
        role = Role(
            name=request.POST.get('name'),
            can_create_tickets='can_create_tickets' in request.POST,
            can_view_all_tickets='can_view_all_tickets' in request.POST,
            can_change_ticket_status='can_change_ticket_status' in request.POST,
            can_assign_master='can_assign_master' in request.POST,
            can_manage_users='can_manage_users' in request.POST,
            can_manage_roles='can_manage_roles' in request.POST,
            can_view_stats='can_view_stats' in request.POST,
        )
        role.save()
        messages.success(request, f'Роль "{role.name}" создана')
        return redirect('role_list')

    return render(request, 'admin/role_form.html', {'action': 'create'})


def role_update(request, pk):
    user_type = request.session.get('user_type')
    if user_type != 'admin':
        messages.error(request, 'Доступ запрещён')
        return redirect('dashboard')

    role = get_object_or_404(Role, pk=pk)

    if request.method == 'POST':
        role.name = request.POST.get('name')
        role.can_create_tickets = 'can_create_tickets' in request.POST
        role.can_view_all_tickets = 'can_view_all_tickets' in request.POST
        role.can_change_ticket_status = 'can_change_ticket_status' in request.POST
        role.can_assign_master = 'can_assign_master' in request.POST
        role.can_manage_users = 'can_manage_users' in request.POST
        role.can_manage_roles = 'can_manage_roles' in request.POST
        role.can_view_stats = 'can_view_stats' in request.POST
        role.save()
        messages.success(request, f'Роль "{role.name}" обновлена')
        return redirect('role_list')

    return render(request, 'admin/role_form.html', {'role': role, 'action': 'update'})


def role_delete(request, pk):
    user_type = request.session.get('user_type')
    if user_type != 'admin':
        messages.error(request, 'Доступ запрещён')
        return redirect('dashboard')

    role = get_object_or_404(Role, pk=pk)

    if request.method == 'POST':
        role_name = role.name
        role.delete()
        messages.success(request, f'Роль "{role_name}" удалена')
        return redirect('role_list')

    return render(request, 'admin/role_confirm_delete.html', {'role': role})