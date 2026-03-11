from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .models import Request, Comment
from accounts.models import Client, Master, User


def dashboard(request):
    user_id = request.session.get('user_id')
    user_type = request.session.get('user_type')

    if not user_id:
        return redirect('login')

    context = {}

    if user_type == 'client':
        client = Client.objects.get(user_id=user_id)
        context['requests'] = Request.objects.filter(client=client).order_by('-start_date')
    elif user_type == 'master':
        master = Master.objects.get(user_id=user_id)
        context['requests'] = Request.objects.filter(master=master).order_by('-start_date')
    else:  # admin
        context['requests'] = Request.objects.all().order_by('-start_date')

    return render(request, 'requests/dashboard.html', context)


def request_list(request):
    user_id = request.session.get('user_id')
    user_type = request.session.get('user_type')

    if not user_id:
        return redirect('login')

    if user_type == 'client':
        client = Client.objects.get(user_id=user_id)
        requests = Request.objects.filter(client=client)
    elif user_type == 'master':
        master = Master.objects.get(user_id=user_id)
        requests = Request.objects.filter(master=master)
    else:
        requests = Request.objects.all()

    # Фильтрация
    status = request.GET.get('status')
    if status == 'completed':
        requests = requests.filter(request_status=True)
    elif status == 'pending':
        requests = requests.filter(request_status=False)

    return render(request, 'requests/request_list.html', {'requests': requests})


def request_create(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    if request.method == 'POST':
        client = Client.objects.get(user_id=user_id)

        new_request = Request(
            start_date=timezone.now(),
            home_tech_type=request.POST.get('home_tech_type'),
            home_tech_model=request.POST.get('home_tech_model'),
            problem_description=request.POST.get('problem_description'),
            request_status=False,
            client=client
        )
        new_request.save()

        messages.success(request, 'Заявка успешно создана!')
        return redirect('request_detail', pk=new_request.request_id)

    return render(request, 'requests/request_form.html')


def request_detail(request, pk):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    req = get_object_or_404(Request, request_id=pk)
    comments = Comment.objects.filter(request=req).order_by('-created_at')
    masters = Master.objects.all() if request.session.get('user_type') == 'admin' else None

    return render(request, 'requests/request_detail.html', {
        'request': req,
        'comments': comments,
        'masters': masters
    })


def request_update(request, pk):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    req = get_object_or_404(Request, request_id=pk)
    user_type = request.session.get('user_type')

    if request.method == 'POST':
        if user_type == 'admin' or user_type == 'master':
            req.request_status = 'request_status' in request.POST
            if req.request_status and not req.completion_date:
                req.completion_date = timezone.now()

            req.repair_parts = request.POST.get('repair_parts', '')

            master_id = request.POST.get('master')
            if master_id:
                req.master = Master.objects.get(master_id=master_id)

            req.save()
            messages.success(request, 'Заявка обновлена')

        return redirect('request_detail', pk=req.request_id)

    return redirect('request_detail', pk=req.request_id)


def add_comment(request, pk):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    if request.method == 'POST':
        req = get_object_or_404(Request, request_id=pk)
        master = Master.objects.get(user_id=user_id)

        comment = Comment(
            message=request.POST.get('message'),
            request=req,
            master=master
        )
        comment.save()
        messages.success(request, 'Комментарий добавлен')

    return redirect('request_detail', pk=pk)