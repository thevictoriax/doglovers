# Любителі собак 🐾

Цей проєкт було створено з метою забезпечення власників собак зручною та інтерактивною платформою для догляду за собаками, отримання інформації та обміну досвідом і порадами. Завдяки сучасному функціоналу вебзастосунок відповідає вимогам цифрової епохи та об'єднує в собі інформаційні, організаційні та соціальні елементи.

# Опис проєкту 📋
"Любителі собак" — це інтерактивна платформа, яка забезпечує власників собак корисною інформацією, організаційними інструментами та можливостями для взаємодії зі спільнотою:

• Допомагає власникам собак отримувати актуальні знання.

• Забезпечує організацію догляду за домашніми улюбленцями.

• Створює простір для обміну досвідом між учасниками спільноти

# Функціонал ✨
 ### Організація догляду:

1. Керування профілями собак:

    Додавання інформації про ваших улюбленців, включно з породою, датою народження, вагою тощо.

2. Інтерактивний календар подій:

    Планування вакцинацій, візитів до ветеринара, грумінгу та інших заходів.

3. Нагадування про важливі події:

    Автоматична система нагадувань забезпечує контроль ключових моментів догляду.

4. Інтерактивна карта:

    Пошук нових місць для прогулянок із собаками.


### Взаємодія з контентом:
1. Закладки, вподобання та коментарі:

    Збереження цікавих статей, ставлення вподобань, участь у дискусіях через коментарі.

2. Пошук контенту:

    Швидке знаходження інформації за тегами, назвою статті чи автором.

3. Додавання власних статей:

    Створення контенту та обговорення важливих тем зі спільнотою.
   

# Встановлення 🌟
Для локального розгортання вебзастосунку:

### Клонування репозиторію:
 
 1. Склонуйте репозиторій:
    
  ``` bash 
  git clone https://github.com/thevictoriax/doglovers.git
```

2. Перейдіть до директорії проекту:
   
     ``` bash 
    cd doglovers
    ```

### Створення та налаштування віртуального середовища:

Рекомендовано використовувати віртуальне середовище для встановлення залежностей:

  ``` bash 
  python -m venv venv
```

Активуйте віртуальне середовище:

  ``` bash 
  venv\Scripts\activate
```

### Установка залежностей:

Встановіть всі необхідні пакети з requirements.txt:

  ``` bash 
  pip install -r requirements.txt
```

### Налаштування бази даних PostgreSQL:

Створення бази даних

  ``` sql 
  CREATE DATABASE DogLovers;
```

Відновлення резервної копії

Завантажте [файл]([url](https://drive.google.com/file/d/1Z0bpDEAVlIFQapxfixHJQ6176Rjo52pu/view?usp=sharing)) і виконайте команду для відновлення

  ``` bash 
  psql -U postgres -d DogLovers -f path/to/doglovers_db.sql
```

### Налаштування файлу settings.py:

Оскільки файл settings.py знаходиться у .gitignore, вам потрібно створити його вручну. Використовуйте наведений нижче приклад із внесеними змінами:

  ``` sql 
  # Файл settings.py

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'ваш_секретний_ключ'  # Замініть на власний секретний ключ

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']  # Додайте домен вашого хосту

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'ckeditor',
    'ckeditor_uploader',
    'django_cron',
    'app.apps.AppConfig',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'DogLovers',  # Назва бази даних
        'USER': 'postgres',   # Ваш PostgreSQL користувач
        'PASSWORD': 'ваш_пароль',  # Пароль для PostgreSQL
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# EMAIL налаштування для SMTP
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'ваш_емейл'
EMAIL_HOST_PASSWORD = 'ваш_пароль'

# Решта параметрів залишаються без змін
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static',]
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'upload'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
CKEDITOR_UPLOAD_PATH = 'uploads/'
CRON_CLASSES = ['app.cron.RemindEventsCronJob',]
```

Збережіть файл як settings.py у відповідній директорії "C:\Users\...\doglovers\doglovers\settings.py".

### Виконання міграцій:

Виконайте міграції, щоб синхронізувати структуру бази даних з Django:

  ``` bash 
  python manage.py makemigrations
python manage.py migrate
```

### Створення суперкористувача:
Створіть адміністративний обліковий запис для доступу до панелі адміністратора:

  ``` bash 
  python manage.py createsuperuser
```

### Запуск локального сервера

  ``` bash 
  python manage.py runserver
```


# Зворотній зв’язок ✉️
Якщо у вас є ідеї, пропозиції або ви бажаєте повідомити про баги, створіть Issue.

Долучайтеся до спільноти "Любителі собак", щоб разом зробити життя собак та їхніх господарів ще комфортнішим! 🐾
