import os
from pathlib import Path

import dj_database_url
import environ
from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent

environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

env = environ.Env(
    ALLOWED_HOSTS=(list, []),
    CSRF_COOKIE_SECURE=(bool, True),
    DATABASE_CONN_MAX_AGE=(int, 600),
    DATABASE_SSL_REQUIRE=(bool, True),
    DEBUG=(bool, False),  # fail closed — never default to True
    SESSION_COOKIE_SECURE=(bool, True),
    SECURE_HSTS_SECONDS=(int, 60 * 60 * 24 * 365),
    SECURE_SSL_REDIRECT=(bool, True),
)

SECRET_KEY = env("SECRET_KEY")  # no default: unset must crash at startup
ENVIRONMENT = env("ENVIRONMENT", default="prod")  # safest branch when unset
APP_VERSION = "2026.1.0"  # kept in sync with pyproject by /release
DEBUG = env.bool("DEBUG")
ALLOWED_HOSTS: list[str] = env("ALLOWED_HOSTS")

ROOT_URLCONF = "core.urls"
WSGI_APPLICATION = "core.wsgi.application"
ASGI_APPLICATION = "core.asgi.application"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.sites",
    "django.contrib.staticfiles",
    # Lets the TemplatesSetting renderer find the built-in widget templates
    "django.forms",
    # THIRD PARTY
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "crispy_forms",
    "crispy_tailwind",
    "dbbackup",
    "django_browser_reload",
    "django_cotton.apps.SimpleAppConfig",
    "django_extensions",
    "django_htmx",
    "django_q",
    "django_tailwind_cli",
    "pwa",
    "storages",
    # INTERNAL
    "accounts",
    "intake",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.auth.middleware.LoginRequiredMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "django_browser_reload.middleware.BrowserReloadMiddleware",
]

# APP_DIRS is False on purpose: the explicit loaders list below wraps cotton in the
# cached loader, which Django would otherwise silently drop.
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": False,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
            "loaders": [
                (
                    "django.template.loaders.cached.Loader",
                    [
                        "django_cotton.cotton_loader.Loader",
                        "django.template.loaders.filesystem.Loader",
                        "django.template.loaders.app_directories.Loader",
                    ],
                )
            ],
            "builtins": ["django_cotton.templatetags.cotton"],
        },
    },
]

FORM_RENDERER = "django.forms.renderers.TemplatesSetting"

# DJANGO CRISPY FORMS
CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
CRISPY_TEMPLATE_PACK = "tailwind"

# DJANGO-TAILWIND-CLI
TAILWIND_CLI_SRC_CSS = "src/source.css"
TAILWIND_CLI_USE_DAISY_UI = True

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_URL = "/static/"
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

LANGUAGE_CODE = "it"
LANGUAGES = (("it", _("Italian")), ("en", _("English")))
LOCALE_PATHS = [BASE_DIR / "locale/"]
TIME_ZONE = "Europe/Rome"
USE_I18N = True
USE_TZ = True

DATE_INPUT_FORMATS = ["%d/%m/%Y", "%Y-%m-%d"]

# PWA
PWA_APP_NAME = "OpenSeat"
PWA_APP_DESCRIPTION = "Event bookings and membership roster for non-profit associations"
PWA_APP_THEME_COLOR = "#1d4ed8"
PWA_APP_BACKGROUND_COLOR = "#ffffff"
PWA_APP_DISPLAY = "standalone"
PWA_APP_SCOPE = "/"
PWA_APP_START_URL = "/"
PWA_APP_ORIENTATION = "any"
PWA_APP_LANG = "it-IT"
PWA_APP_ICONS = [{"src": "/static/images/icon-512.png", "sizes": "512x512"}]
PWA_SERVICE_WORKER_PATH = BASE_DIR / "static" / "js" / "serviceworker.js"

# ALLAUTH
AUTH_USER_MODEL = "accounts.CustomUser"  # email-based, no username field
LOGIN_REDIRECT_URL = "/"
SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*"]
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_PRESERVE_USERNAME_CASING = False
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_EMAIL_SUBJECT_PREFIX = "OpenSeat - "

# Register Google only when credentials are present, so an install without OAuth
# hides the button instead of raising.
SOCIALACCOUNT_PROVIDERS: dict = {}
if GOOGLE_OAUTH_CLIENT_ID := env("GOOGLE_OAUTH_CLIENT_ID", default=""):
    SOCIALACCOUNT_PROVIDERS["google"] = {
        "APP": {
            "client_id": GOOGLE_OAUTH_CLIENT_ID,
            "secret": env("GOOGLE_OAUTH_CLIENT_SECRET", default=""),
            "key": "",
        },
        "SCOPE": ["profile", "email"],
        "VERIFIED_EMAIL": True,  # skip the redundant confirmation step
    }
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True
SOCIALACCOUNT_LOGIN_ON_GET = True

DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@localhost")

# DBBACKUP — pick a remote backend per project and put its credentials in
# .env.example. Left on the local filesystem here on purpose.
DBBACKUP_STORAGE = "django.core.files.storage.FileSystemStorage"
DBBACKUP_STORAGE_OPTIONS = {"location": str(BASE_DIR / "backups")}
DBBACKUP_CLEANUP_KEEP = 10
DBBACKUP_CLEANUP_KEEP_MEDIA = 10

Q_CLUSTER_BASE = {
    "name": "openseat",
    "workers": env.int("Q_CLUSTER_WORKERS", default=4),
    "timeout": env.int("Q_CLUSTER_TIMEOUT", default=300),
    "retry": env.int("Q_CLUSTER_RETRY", default=600),  # keep above timeout
    "max_attempts": env.int("Q_CLUSTER_MAX_ATTEMPTS", default=3),
    "queue_limit": env.int("Q_CLUSTER_QUEUE_LIMIT", default=50),
    "save_limit": 250,
    "catch_up": False,
}

if ENVIRONMENT == "dev":
    DEBUG = True
    INTERNAL_IPS = ["127.0.0.1"]
    # Dev-only dependency: importing it in prod would fail, the wheel isn't there.
    INSTALLED_APPS += ["django_crawl"]
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
            "ATOMIC_REQUESTS": True,
            "CONN_MAX_AGE": 0,
            "OPTIONS": {"init_command": "PRAGMA foreign_keys=ON;"},
        }
    }
    Q_CLUSTER = {**Q_CLUSTER_BASE, "orm": "default"}
    MAILERS = {
        "default": {
            "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
            "OPTIONS": {
                "host": env("EMAIL_HOST", default="localhost"),
                "port": env.int("EMAIL_PORT", default=1025),
                "use_tls": False,
            },
        },
    }

elif ENVIRONMENT == "test":
    DATABASES = {
        "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}
    }
    PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
    Q_CLUSTER = {**Q_CLUSTER_BASE, "sync": True}  # tasks run inline
    MAILERS = {
        "default": {"BACKEND": "django.core.mail.backends.locmem.EmailBackend"},
    }

else:  # prod
    DATABASES = {
        "default": dj_database_url.config(
            conn_max_age=env("DATABASE_CONN_MAX_AGE"),
            ssl_require=env("DATABASE_SSL_REQUIRE"),
        )
    }
    STORAGES["staticfiles"] = {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    }
    Q_CLUSTER = {
        **Q_CLUSTER_BASE,
        "redis": {
            "host": env("REDIS_HOST", default="localhost"),
            "port": env.int("REDIS_PORT", default=6379),
            "db": env.int("REDIS_DB", default=0),
        },
    }
    MAILERS = {
        "default": {"BACKEND": "anymail.backends.mailgun.EmailBackend"},
    }
    ANYMAIL = {
        "MAILGUN_API_KEY": env("MAILGUN_API_KEY", default=""),
        "MAILGUN_API_URL": env(
            "MAILGUN_API_URL", default="https://api.eu.mailgun.net/v3"
        ),
        "MAILGUN_SENDER_DOMAIN": env("MAILGUN_SENDER_DOMAIN", default=""),
    }

# The test branch keeps DEBUG False but must not redirect to HTTPS, or every
# test client request answers 301 before reaching a view.
if not DEBUG and ENVIRONMENT != "test":
    CSRF_COOKIE_SECURE = env("CSRF_COOKIE_SECURE")
    SESSION_COOKIE_SECURE = env("SESSION_COOKIE_SECURE")
    SECURE_SSL_REDIRECT = env("SECURE_SSL_REDIRECT")
    SECURE_HSTS_SECONDS = env("SECURE_HSTS_SECONDS")
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
