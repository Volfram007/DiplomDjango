from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import get_object_or_404, render, redirect
from InitText import *
from Forum.models import *


def index(request):
    """ Главная страница """
    context = {
        'TitlePage': IndexTitle,
        'TextPage': IndexText,
        'btnHomeVisible': False,
        'btnAuthenticatedVisible': True,
    }

    if request.user.is_authenticated:
        fotos_sort_date = {}
        fotos = ImageModel.objects.filter(user=request.user).order_by('-date')
        print(fotos)
        # Группировка фотографий по дате
        for foto in fotos:
            date_str = foto.date.strftime('%d.%m.%Y')
            if date_str not in fotos_sort_date:
                fotos_sort_date[date_str] = []
            fotos_sort_date[date_str].append(foto)

        # Словарь в список (дата, список фото)
        fotos_list = list(fotos_sort_date.items())
        print(fotos_list)
        paginator = Paginator(fotos_list, 3)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['page_obj'] = page_obj
    else:
        context['AnonymousUser'] = AnonymousUser
    return render(request, 'index.html', context)


@login_required
def user_logout(request):
    # Очистка всех данных сессии
    logout(request)
    return redirect('authorization')


def authorization(request):
    """ Авторизация и регистрация """
    # Проверка на авторизацию
    if request.user.is_authenticated:
        # Переход на домашнюю страницу
        return redirect('index')

    context = {
        'TitlePage': 'Авторизация',
        'btnHomeVisible': True,
        'btnAuthenticatedVisible': False,
    }

    if request.method == 'POST':
        # Считываем тип активной формы (Вход/Регистрация)
        form_type = request.POST.get('form_act')
        # Получаем логин и пароль
        username = request.POST.get('username')
        password1 = request.POST.get('password1')

        if form_type == 'login':
            # Проверяет существование пользователя с проверкой пароля
            user = authenticate(request, username=username, password=password1)
            # Если пользователь существует, то авторизуем его
            if user is not None:
                login(request, user)
                return redirect('index')
            else:
                context['error'] = Error_LoginOrPassword

        elif form_type == 'register':
            # Получаем подтверждение пароля
            password2 = request.POST.get('password2')
            import re

            # Проверка на заполнение всех полей
            if not username or not password1 or not password2:
                context['error'] = Error_AllFieldsRequired
            # Проверка одинаковых паролей
            elif password1 != password2:
                context['error'] = Error_PasswordsNotMatch
            # Проверка на совпадение логина
            elif User.objects.filter(username=username).exists():
                context['error'] = Error_UserExists
            # Проверка длины пароля
            elif len(password1 or password2) <= Min_Password_Length:
                context['error'] = Error_Password_Length
            else:
                # Создаем нового пользователя
                user = User(username=username, password=make_password(password1))
                user.save()
                # Автоматически входим в аккаунт
                login(request, user)
                return redirect('index')
            # Активируем форму регистрации если была ошибка
            context['form_act'] = 'register'
    return render(request, 'authorization.html', context)


def get_random_date():
    # Генерируем случайное смещение от текущей даты
    import random
    from datetime import timedelta
    from django.utils import timezone

    random_days = random.randint(-5, 0)
    date = timezone.now() + timedelta(days=random_days)
    return date


@login_required
def upload_file(request):
    # Проверка на авторизацию
    if not request.user.is_authenticated:
        return redirect('authorization')

    # Получаем файл
    if request.method == 'POST':
        from django.utils import timezone

        # Получаем файлы и сохраняем
        for uploaded_file in request.FILES.getlist('uploaded_files'):
            # Устанавливаем случайную дату
            file_date = get_random_date()
            # Сохраняем каждый файл с датой файла
            foto = ImageModel(user=request.user, image=uploaded_file, date=file_date)
            foto.save()

    return redirect('index')


@login_required
def delete_image(request, image_id):
    image = get_object_or_404(ImageModel, id=image_id, user=request.user)
    image.delete()
    return redirect('index')
