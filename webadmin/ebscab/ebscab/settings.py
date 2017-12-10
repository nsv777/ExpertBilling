# -*- coding: utf-8 -*-

import logging
import os
import sys

from django.contrib.messages import constants as messages_constants
from django.utils.translation import ugettext_lazy as _
from tzlocal import get_localzone


sys.path.append('/opt/ebs/data/workers/')

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEBUG = True
DEBUG_SQL = False
USE_TZ = False

ADMINS = (
    #('Your Name', 'your_email@domain.com'),
)
MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'ATOMIC_REQUESTS': True,
        'NAME': 'ebs',
        'USER': 'ebs',
        'PASSWORD': 'ebspassword',
        'HOST': '127.0.0.1',
        'PORT': 5432
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211'
    }
}

TIME_ZONE = get_localzone().zone

LANGUAGES = [
    ('ru', _('Русский')),
    ('en', _('Английский'))
]

LANGUAGE_CODE = 'ru-RU'

SITE_ID = 1

USE_I18N = True

USE_l10N = True

DATETIME_FORMAT = 'd.m.Y H:i:s'
SHORT_DATETIME_FORMAT = 'd.m.Y H:i:s'

STATIC_URL = '/static/'
STATIC_ROOT = '/opt/ebs/web/ebscab/files/static'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static')
]
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder'
]

MEDIA_URL = '/media/'
MEDIA_ROOT = '/opt/ebs/web/ebscab/files/media'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '%!a5^gik_4lgzt+k)vyo6)y68_3!u^*j(ujks7(=6f2j89d=x&'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            '/opt/ebs/web/ebscab/templates',
            os.path.join(BASE_DIR, 'templates')
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.request',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.i18n',
                'django.contrib.messages.context_processors.messages',
                'ebscab.context_processors.default_current_view_name',
                'ebscab.context_processors.project_settings'
            ]
        }
    }
]

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.admindocs.middleware.XViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'ebsadmin.middleware.Version'
)

ROOT_URLCONF = 'ebscab.urls'

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale')
]

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.admin',
    'django.contrib.staticfiles',
    'radius',
    'nas',
    'billservice',
    'statistics',
    'helpdesk',
    'object_log',
    'django_tables2',
    'crispy_forms',
    'dynamicmodel',
    'ajax_select',
    'ebsadmin',
    'django_tables2_reports',
    'getpaid',
    'sendsms',
    'autocomplete_light',
    'selectable',
    'mathfilters',
    'captcha',
    'cassa',
    'ebsweb'
]

MESSAGE_TAGS = {
    messages_constants.DEBUG: 'default',
    messages_constants.ERROR: 'danger'
}

AJAX_LOOKUP_CHANNELS = {
    #   pass a dict with the model and the field to search against
    'account_fts': ('billservice.lookups', 'AccountFTSLookup'),
    'account_fullname': ('billservice.lookups', 'AccountFullnameLookup'),
    'account_username': ('billservice.lookups', 'AccountUsernameLookup'),
    'account_contract': ('billservice.lookups', 'AccountContractLookup'),
    'account_contactperson': ('billservice.lookups', 'AccountContactPersonLookup'),
    'city_name': ('billservice.lookups', 'CityLookup'),
    'street_name': ('billservice.lookups', 'StreetLookup'),
    'house_name': ('billservice.lookups', 'HouseLookup'),
    'hardware_fts': ('billservice.lookups', 'HardwareLookup'),
    'organization_name': ('billservice.lookups', 'OrganizationLookup'),
    'subaccount_fts': ('billservice.lookups', 'SubAccountFTSLookup')
}

AJAX_SELECT_BOOTSTRAP = False
AJAX_SELECT_INLINES = 'inline'

AUTHENTICATION_BACKENDS = (
    'billservice.backend.LoginUserBackend',
)

# credentials generation rules
LOGIN_LENGTH = 8
PASSWORD_LENGTH = 8
LOGIN_CONTAIN_LETTERS = True
LOGIN_CONTAIN_DIGITS = True
PASSWORD_CONTAIN_LETTERS = False
PASSWORD_CONTAIN_DIGITS = True

PGCRYPTO_VALID_CIPHERS = ('AES',)
PGCRYPTO_DEFAULT_CIPHER = 'AES'
PGCRYPTO_DEFAULT_KEY = 'ebscryptkeytest'

LOG_LEVEL = 0

SESSION_EXPIRE_AT_BROWSER_CLOSE = True

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/login/'

ALLOW_PROMISE = True
MAX_PROMISE_SUM = 10000
MIN_BALLANCE_FOR_PROMISE = -1000
LEFT_PROMISE_DAYS = 7
PROMISE_REACTIVATION_DAYS = 28

# NOTE: aliases for 'ebsweb'
PROMISE_ALLOWED = ALLOW_PROMISE
PROMISE_MAX_SUM = MAX_PROMISE_SUM
PROMISE_MIN_BALANCE = MIN_BALLANCE_FOR_PROMISE
PROMISE_LEFT_DAYS = LEFT_PROMISE_DAYS
PROMISE_AGAIN_DAYS = PROMISE_REACTIVATION_DAYS

ALLOW_WEBMONEY = False
ALLOW_QIWI = False
QIWI_MIN_SUMM = 30

EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'user@gmail.com'
EMAIL_HOST_PASSWORD = 'userpassword'

HIDE_PASSWORDS = False
ENABLE_SELECT2_MULTI_PROCESS_SUPPORT = False
CURRENCY = u' руб'

HOTSPOT_ONLY_PIN = False
GETPAID_BACKENDS = []
PROVIDER_LOGO = 'img/ebs.jpg'  # store in STATIC_ROOT
GETPAID_BACKENDS_SETTINGS = {
    # Please provide your settings for backends
    'payments.liqpay': {
        'TYPE': 'frontend',
        'DEFAULT_CURRENCY': 'UAH',
        'MERCHANT_ID': '',
        'MERCHANT_SIGNATURE': '',
        'PAY_WAY': ('card', 'liqpay', 'delayed'),
        'EXPIRE_TIME': 36
    },
    'payments.easypay': {
        'TYPE': 'backend',
        'DEFAULT_CURRENCY': 'UAH',
        'SERVICE_ID': '1',
        'allowed_ip': ('93.183.196.28', '93.183.196.26')
    },
    'payments.ru_sberbank': {
        'TYPE': 'backend',
        'DEFAULT_CURRENCY': 'RUB',
        'PASSWORD': '12345',
        'allowed_ip': ('93.183.196.28', '93.183.196.26')
    },
    'payments.masterplat': {
        'TYPE': 'backend',
        'DEFAULT_CURRENCY': 'RUB',
        'DUSER': '12345',
        'DPASS': '12345'
    },
    'payments.platezhkaua': {
        'TYPE': 'backend',
        'DEFAULT_CURRENCY': 'UAH',
        'LOGIN': '12345',
        'PASSWORD': '12345'
    },
    'payments.yandexcassa': {}
}

SENDSMS_BACKENDS = (
    ('sendsms.backends.websms.SmsBackend', 'websms.ru'),
    ('sendsms.backends.smsru.SmsBackend', 'sms.ru'),
    ('sendsms.backends.smspilotru.SmsBackend', 'smspilot.ru')
)

SENDSMS_BACKENDS_SETTINGS = {
    'sendsms.backends.websms': {
        'FROM_NAME': '',  # http://websms.ru/FromName.asp
        'USERNAME': '',
        'PASSWORD': ''
    },
    'sendsms.backends.smsru': {
        'FROM_NAME': '',
        'API_ID': '',
        'TRANSLIT': '1',
        'TEST': '0',
        'PARTNER_ID': ''
    },
    'sendsms.backends.smspilotru': {
        'FROM_NAME': '',
        'API_ID': ''
    }
}

SENDSMS_IF_BALLANCE_AMOUNT = 0
SENDSMS_NOT_SEND_IF_BALANCE_LESS = -10000
SENDSMS_SEND_EVERY_N_DAY = 5
SENDSMS_DEFAULT_BACKEND = 'sendsms.backends.websms.SmsBackend'
SENDSMS_DEFAULT_FROM_PHONE = '+11111111111'

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

CAPTCHA_FONT_SIZE = 18
CAPTCHA_LETTER_ROTATION = (-1, 1)
CAPTCHA_NOISE_FUNCTIONS = ('captcha.helpers.noise_dots',)

PERSONAL_AREA_STAFF_MENU = [
    ('helpdesk_dashboard', u'Сводка', ''),
    ('helpdesk_list', u'Заявки', ''),
    ('helpdesk_submit', u'Создать заявку', 'modal-queue-dialog'),
    ('helpdesk_kb_index', u'База знаний', ''),
    ('helpdesk_report_index', u'Статистика', ''),
    ('helpdesk_user_settings', u'Ваши настройки', ''),
    ('/admin/', u'Конфигурация', ''),
    ('account_logout', u'Выход', '')
]


# load local_settings
try:
    from settings_local import *
    import settings_local
    if 'GETPAID_BACKENDS' in settings_local.__dict__:
        INSTALLED_APPS += settings_local.GETPAID_BACKENDS
except Exception, ex:
    print(ex)


# define logging
# TODO: remake follow https://docs.djangoproject.com/en/1.11/topics/logging/
if DEBUG:
    LEVEL = logging.DEBUG
else:
    LEVEL = logging.INFO
logging.basicConfig(level=LEVEL,
                    format='%(asctime)s %(name)s %(levelname)s %(message)s',
                    filename=os.path.join(BASE_DIR, 'log/django.log'),
                    filemode='a+')