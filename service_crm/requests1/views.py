from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db import models as db_models
from .models import Request, Comment
from accounts.models import Client, Master, User


# Декоратор для проверки авторизации
def login_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('user_id'):
            messages.error(request, 'Необходимо войти в систему')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


# Декоратор для проверки роли
def role_required(allowed_types):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            user_type = request.session.get('user_type')
            if user_type not in allowed_types:
                messages.error(request, 'У вас нет прав для доступа к этой странице')
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# Главная страница - дашборд
@login_required
def dashboard(request):
    user_id = request.session.get('user_id')
    user_type = request.session.get('user_type')
    user = User.objects.get(user_id=user_id)

    context = {}

    if user_type == 'client':
        client = Client.objects.get(user_id=user_id)
        requests_qs = Request.objects.filter(client=client).order_by('-start_date')
        context['requests'] = requests_qs
        context['total_requests'] = requests_qs.count()
        context['new_requests'] = requests_qs.filter(request_status='new').count()
        context['in_progress_requests'] = requests_qs.filter(request_status='in_progress').count()
        context['completed_requests'] = requests_qs.filter(request_status='completed').count()
        context['ready_requests'] = requests_qs.filter(request_status='ready').count()

    elif user_type == 'master':
        master = Master.objects.get(user_id=user_id)
        requests_qs = Request.objects.filter(master=master).order_by('-start_date')
        context['requests'] = requests_qs
        context['total_requests'] = requests_qs.count()
        context['new_requests'] = requests_qs.filter(request_status='new').count()
        context['in_progress_requests'] = requests_qs.filter(request_status='in_progress').count()
        context['completed_requests'] = requests_qs.filter(request_status='completed').count()

    elif user_type == 'admin':
        requests_qs = Request.objects.all().order_by('-start_date')
        context['requests'] = requests_qs
        context['total_requests'] = requests_qs.count()
        context['new_requests'] = requests_qs.filter(request_status='new').count()
        context['pending_requests'] = requests_qs.filter(request_status='pending').count()
        context['in_progress_requests'] = requests_qs.filter(request_status='in_progress').count()
        context['ready_requests'] = requests_qs.filter(request_status='ready').count()
        context['completed_requests'] = requests_qs.filter(request_status='completed').count()
        context['cancelled_requests'] = requests_qs.filter(request_status='cancelled').count()
        context['total_clients'] = Client.objects.count()
        context['total_masters'] = Master.objects.count()

    return render(request, 'requests/dashboard.html', context)


# Список всех заявок (с фильтрацией)
@login_required
def request_list(request):
    user_id = request.session.get('user_id')
    user_type = request.session.get('user_type')

    # Базовый запрос в зависимости от роли
    if user_type == 'client':
        client = Client.objects.get(user_id=user_id)
        requests_qs = Request.objects.filter(client=client)
    elif user_type == 'master':
        requests_qs = Request.objects.all()  # Мастер видит все заявки
    else:  # admin
        requests_qs = Request.objects.all()

    # Фильтрация по статусу
    status = request.GET.get('status')
    if status and status != 'all':
        requests_qs = requests_qs.filter(request_status=status)

    # Фильтрация по мастеру (для админа)
    master_id = request.GET.get('master')
    if master_id and user_type == 'admin':
        requests_qs = requests_qs.filter(master_id=master_id)

    # Поиск по номеру заявки или описанию
    search = request.GET.get('search')
    if search:
        try:
            search_int = int(search)
            requests_qs = requests_qs.filter(
                db_models.Q(request_id=search_int) |
                db_models.Q(problem_description__icontains=search) |
                db_models.Q(home_tech_type__icontains=search) |
                db_models.Q(home_tech_model__icontains=search)
            )
        except ValueError:
            requests_qs = requests_qs.filter(
                db_models.Q(problem_description__icontains=search) |
                db_models.Q(home_tech_type__icontains=search) |
                db_models.Q(home_tech_model__icontains=search)
            )

    # Сортировка
    sort = request.GET.get('sort', '-start_date')
    requests_qs = requests_qs.order_by(sort)

    # Для админа - список мастеров для фильтра
    masters = None
    if user_type == 'admin':
        masters = Master.objects.all()

    status_choices = Request.STATUS_CHOICES

    return render(request, 'requests/request_list.html', {
        'requests': requests_qs,
        'masters': masters,
        'current_status': status,
        'current_sort': sort,
        'search_query': search,
        'status_choices': status_choices,
    })


# Детальный просмотр заявки
@login_required
def request_detail(request, pk):
    user_id = request.session.get('user_id')
    user_type = request.session.get('user_type')

    req = get_object_or_404(Request, request_id=pk)

    # Проверка прав доступа
    if user_type == 'client':
        client = Client.objects.get(user_id=user_id)
        if req.client.client_id != client.client_id:
            messages.error(request, 'У вас нет доступа к этой заявке')
            return redirect('dashboard')

    comments = Comment.objects.filter(request=req).order_by('-created_at')

    # Для админа - список всех мастеров
    masters = None
    if user_type == 'admin':
        masters = Master.objects.all()

    # Для мастера - только если заявка назначена ему или никому
    is_assigned = False
    if user_type == 'master':
        master = Master.objects.get(user_id=user_id)
        is_assigned = (req.master is None) or (req.master.master_id == master.master_id)

    status_choices = Request.STATUS_CHOICES

    return render(request, 'requests/request_detail.html', {
        'ticket': req,
        'comments': comments,
        'masters': masters,
        'is_assigned': is_assigned,
        'status_choices': status_choices,
    })


# Создание заявки (только для клиента)
@login_required
@role_required(['client'])
def request_create(request):
    user_id = request.session.get('user_id')
    client = Client.objects.get(user_id=user_id)

    if request.method == 'POST':
        new_request = Request(
            start_date=timezone.now(),
            home_tech_type=request.POST.get('home_tech_type'),
            home_tech_model=request.POST.get('home_tech_model'),
            problem_description=request.POST.get('problem_description'),
            request_status='new',
            client=client
        )
        new_request.save()

        messages.success(request, f'Заявка #{new_request.request_id} успешно создана!')
        return redirect('request_detail', pk=new_request.request_id)

    return render(request, 'requests/request_form.html', {
        'action': 'create',
        'status_choices': Request.STATUS_CHOICES,
    })


# Редактирование заявки
@login_required
def request_update(request, pk):
    user_id = request.session.get('user_id')
    user_type = request.session.get('user_type')

    req = get_object_or_404(Request, request_id=pk)

    # Проверка прав
    if user_type == 'client':
        messages.error(request, 'У вас нет прав для редактирования заявок')
        return redirect('request_detail', pk=pk)

    if user_type == 'master':
        master = Master.objects.get(user_id=user_id)
        # Мастер может менять только свои заявки или неназначенные
        if req.master and req.master.master_id != master.master_id:
            messages.error(request, 'Вы можете редактировать только свои заявки')
            return redirect('request_detail', pk=pk)

    if request.method == 'POST':
        # Мастер может менять статус и запчасти
        if user_type == 'master':
            new_status = request.POST.get('request_status')
            if new_status:
                req.request_status = new_status
                # Если статус "завершена" или "готова", ставим дату завершения
                if new_status in ['completed', 'ready'] and not req.completion_date:
                    req.completion_date = timezone.now()
                elif new_status not in ['completed', 'ready']:
                    req.completion_date = None
            req.repair_parts = request.POST.get('repair_parts', '')
            messages.success(request, f'Статус заявки #{pk} обновлен')

        # Админ может менять всё
        elif user_type == 'admin':
            req.home_tech_type = request.POST.get('home_tech_type')
            req.home_tech_model = request.POST.get('home_tech_model')
            req.problem_description = request.POST.get('problem_description')
            new_status = request.POST.get('request_status')
            if new_status:
                req.request_status = new_status
                if new_status in ['completed', 'ready'] and not req.completion_date:
                    req.completion_date = timezone.now()
                elif new_status not in ['completed', 'ready']:
                    req.completion_date = None
            req.repair_parts = request.POST.get('repair_parts', '')

            master_id = request.POST.get('master')
            if master_id:
                req.master = Master.objects.get(master_id=master_id)
            else:
                req.master = None

            messages.success(request, f'Заявка #{pk} полностью обновлена')

        req.save()
        return redirect('request_detail', pk=pk)

    # GET запрос - форма редактирования
    status_choices = Request.STATUS_CHOICES

    if user_type == 'admin':
        masters = Master.objects.all()
        return render(request, 'requests/request_form.html', {
            'ticket': req,
            'masters': masters,
            'action': 'update',
            'status_choices': status_choices,
        })
    else:  # master
        return render(request, 'requests/request_form.html', {
            'ticket': req,
            'action': 'update_master',
            'status_choices': status_choices,
        })


# Удаление заявки (только для админа)
@login_required
@role_required(['admin'])
def request_delete(request, pk):
    req = get_object_or_404(Request, request_id=pk)

    if request.method == 'POST':
        req_id = req.request_id
        req.delete()
        messages.success(request, f'Заявка #{req_id} удалена')
        return redirect('request_list')

    return render(request, 'requests/request_confirm_delete.html', {'ticket': req})


# Назначение мастера на заявку (только для админа)
@login_required
@role_required(['admin'])
def assign_master(request, pk):
    req = get_object_or_404(Request, request_id=pk)

    if request.method == 'POST':
        master_id = request.POST.get('master')
        if master_id:
            master = Master.objects.get(master_id=master_id)
            req.master = master
            req.save()
            messages.success(request, f'Мастер {master.user.fio} назначен на заявку #{pk}')
        else:
            req.master = None
            req.save()
            messages.success(request, f'Мастер снят с заявки #{pk}')

    return redirect('request_detail', pk=pk)


# Добавление комментария (только для мастера)
@login_required
@role_required(['master'])
def add_comment(request, pk):
    user_id = request.session.get('user_id')
    req = get_object_or_404(Request, request_id=pk)
    master = Master.objects.get(user_id=user_id)

    # Проверка, что мастер назначен на эту заявку
    if not req.master or req.master.master_id != master.master_id:
        messages.error(request, 'Вы можете комментировать только свои заявки')
        return redirect('request_detail', pk=pk)

    if request.method == 'POST':
        message = request.POST.get('message')
        if message:
            comment = Comment(
                message=message,
                request=req,
                master=master
            )
            comment.save()
            messages.success(request, 'Комментарий добавлен')

    return redirect('request_detail', pk=pk)


# Управление пользователями (только для админа)
@login_required
@role_required(['admin'])
def user_list(request):
    users = User.objects.all()
    return render(request, 'admin/user_list.html', {'users': users})


@login_required
@role_required(['admin'])
def user_create(request):
    if request.method == 'POST':
        fio = request.POST.get('fio')
        phone = request.POST.get('phone')
        login = request.POST.get('login')
        password = request.POST.get('password')
        user_type = request.POST.get('type')

        if User.objects.filter(login=login).exists():
            messages.error(request, 'Логин уже занят')
            return redirect('user_create')

        user = User.objects.create_user(
            login=login,
            password=password,
            fio=fio,
            phone=phone,
            type=user_type
        )

        if user_type == 'client':
            Client.objects.create(user=user)
        elif user_type == 'master':
            Master.objects.create(user=user)

        messages.success(request, f'Пользователь {fio} создан')
        return redirect('user_list')

    return render(request, 'admin/user_form.html', {'action': 'create'})


@login_required
@role_required(['admin'])
def user_update(request, pk):
    user = get_object_or_404(User, user_id=pk)

    if request.method == 'POST':
        user.fio = request.POST.get('fio')
        user.phone = request.POST.get('phone')
        user.type = request.POST.get('type')

        new_password = request.POST.get('password')
        if new_password:
            user.set_password(new_password)

        user.save()
        messages.success(request, f'Пользователь {user.fio} обновлен')
        return redirect('user_list')

    return render(request, 'admin/user_form.html', {
        'edit_user': user,
        'action': 'update'
    })


@login_required
@role_required(['admin'])
def user_delete(request, pk):
    user = get_object_or_404(User, user_id=pk)

    if request.method == 'POST':
        user_name = user.fio
        user.delete()
        messages.success(request, f'Пользователь {user_name} удален')
        return redirect('user_list')

    return render(request, 'admin/user_confirm_delete.html', {'user': user})


# Статистика для админа
@login_required
@role_required(['admin'])
def admin_stats(request):
    total_requests = Request.objects.count()
    completed_requests = Request.objects.filter(request_status='completed').count()
    new_requests = Request.objects.filter(request_status='new').count()
    in_progress_requests = Request.objects.filter(request_status='in_progress').count()
    ready_requests = Request.objects.filter(request_status='ready').count()
    cancelled_requests = Request.objects.filter(request_status='cancelled').count()

    # Статистика по мастерам
    masters_stats = []
    for master in Master.objects.all():
        master_requests = Request.objects.filter(master=master)
        masters_stats.append({
            'master': master,
            'total': master_requests.count(),
            'completed': master_requests.filter(request_status='completed').count(),
            'in_progress': master_requests.filter(request_status='in_progress').count(),
            'new': master_requests.filter(request_status='new').count(),
        })

    clients_count = Client.objects.count()

    context = {
        'total_requests': total_requests,
        'completed_requests': completed_requests,
        'new_requests': new_requests,
        'in_progress_requests': in_progress_requests,
        'ready_requests': ready_requests,
        'cancelled_requests': cancelled_requests,
        'completion_rate': (completed_requests / total_requests * 100) if total_requests > 0 else 0,
        'masters_stats': masters_stats,
        'clients_count': clients_count,
    }

    return render(request, 'admin/stats.html', context)