import os
from pathlib import Path
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import get_object_or_404, render, redirect
from Forum.models import *

from InitText import *


def index(request):
    context = {
        'TitlePage': IndexTitle,  # Заголовок страницы
        'TextPage': IndexText,  # Текст страницы
        'btnHomeVisible': False,  # Видимость кнопки
        'btnAuthenticatedVisible': True,
    }

    if request.user.is_authenticated:
        fotos_sort_date = {}
        fotos = ImageModel.objects.filter(user=request.user).order_by('-date')
        # Группировка фотографий по дате
        for foto in fotos:
            date_str = foto.date.strftime('%d.%m.%Y')
            # Если строки с этой датой еще нет в словаре, создаем новый ключ с пустым списком
            if date_str not in fotos_sort_date:
                fotos_sort_date[date_str] = []
            fotos_sort_date[date_str].append(foto)

        # Словарь в список (дата, список фото)
        fotos_list = list(fotos_sort_date.items())
        # Создание объекта пагинации
        paginator = Paginator(fotos_list, 3)
        # Получение номера страницы
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
        'TitlePage': 'Авторизация',  # Заголовок страницы
        'btnHomeVisible': True,
        'btnAuthenticatedVisible': False,
    }

    if request.method == 'POST':
        # Получение типа активной формы (вход или регистрация)
        form_type = request.POST.get('form_act')
        # Получаем логин и пароль
        username = request.POST.get('username')
        password1 = request.POST.get('password1')

        if form_type == 'login':
            # Аутентификация пользователя по имени и паролю
            user = authenticate(request, username=username, password=password1)
            # Проверка, успешна ли аутентификация
            if user is not None:
                # Вход пользователя в систему
                login(request, user)
                return redirect('index')
            else:
                # Сообщение об ошибке при неверном логине или пароле
                context['error'] = Error_LoginOrPassword

        # Обработка формы регистрации
        elif form_type == 'register':
            # Получаем подтверждение пароля
            password2 = request.POST.get('password2')
            # Импорт библиотеки для дополнительных проверок
            import re

            # Проверка на заполнение всех полей
            if not username or not password1 or not password2:
                context['error'] = Error_AllFieldsRequired
            # Проверка, совпадают ли введенные пароли
            elif password1 != password2:
                context['error'] = Error_PasswordsNotMatch
            # Проверка на совпадение логина
            elif User.objects.filter(username=username).exists():
                context['error'] = Error_UserExists
            # Проверка длины пароля
            elif len(password1 or password2) <= Min_Password_Length:
                context['error'] = Error_Password_Length
            else:
                # Создание нового пользователя с хешированным паролем
                user = User(username=username, password=make_password(password1))
                user.save()
                # Автоматический вход
                login(request, user)
                return redirect('index')
            # Если произошла ошибка, активируем форму регистрации
            context['form_act'] = 'register'
    return render(request, 'authorization.html', context)


def get_random_date():
    """Генерируем случайное смещение от текущей даты"""
    import random
    from datetime import timedelta
    from django.utils import timezone

    random_days = random.randint(-5, 0)
    date = timezone.now() + timedelta(days=random_days)
    return date


@login_required
def upload_file(request):
    # Проверка авторизации
    if not request.user.is_authenticated:
        return redirect('authorization')

    # Получаем файл
    if request.method == 'POST':
        # Получаем файлы и сохраняем
        for uploaded_file in request.FILES.getlist('uploaded_files'):
            # Генерируем случайную дату
            file_date = get_random_date()
            foto = ImageModel(user=request.user, image=uploaded_file, date=file_date)
            foto.save()
    return redirect('index')


@login_required
def delete_image(request, image_id):
    # Если объект не найден, возвращается ошибка 404.
    image = get_object_or_404(ImageModel, id=image_id, user=request.user)
    # Получение пути к файлу изображения
    image_path = Path(__file__).resolve().parent.parent / 'media' / str(image.image)
    # Удаление объекта из базы данных
    image.delete()
    # Проверка существования файла на диске и его удаление
    if os.path.exists(image_path):
        try:
            os.remove(image_path)
        except Exception as e:
            print(f"Ошибка при удалении файла: {e}")
    # Перенаправление пользователя на главную страницу после удаления изображения
    return redirect('index')
