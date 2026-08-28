import os
from pathlib import Path
from urllib.parse import quote

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
APP_VERSION = "2026.1.4"  # the release series, as the footer shows it
APP_VENDOR = "Webbografico"  # whose build this is, signed in the footer
APP_VENDOR_URL = "https://webbografico.com"
APP_SOURCE_URL = "https://github.com/applewebbo/openseat"
DEBUG = env.bool("DEBUG")
ALLOWED_HOSTS: list[str] = env("ALLOWED_HOSTS")

ROOT_URLCONF = "core.urls"
WSGI_APPLICATION = "core.wsgi.application"
ASGI_APPLICATION = "core.asgi.application"

INSTALLED_APPS = [
    # django.contrib.admin, with the project's own AdminSite as its default
    "core.admin_config.OpenSeatAdminConfig",
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
    "django_ckeditor_5",
    "django_cotton.apps.SimpleAppConfig",
    "django_extensions",
    "django_htmx",
    "django_q",
    "django_tailwind_cli",
    "health_check",
    "import_export",
    "pwa",
    "storages",
    # INTERNAL
    # core holds no models, but it holds the project-level management commands,
    # which Django only discovers inside an installed app.
    "core",
    "accounts",
    "events",
    "intake",
    "members",
    "ops",
]

# WhiteNoise is added by the prod branch alone. In dev, runserver's own static
# handler answers first and WhiteNoise never sees the request; in tests, nothing
# asks for a static file and STATIC_ROOT does not exist until collectstatic runs
# at deploy, so it would warn once per request about a deliberate absence.
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
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
                "core.context_processors.build",
                "core.context_processors.association",
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

# DJANGO-CKEDITOR-5
# One toolbar, deliberately short: the home page description is written by a
# volunteer, and every extra button is one more thing that can break the page.
# The editor ships its own assets with the package — nothing is fetched at runtime.
CKEDITOR_5_CONFIGS = {
    "default": {
        "toolbar": [
            "heading",
            "|",
            "bold",
            "italic",
            "link",
            "|",
            "bulletedList",
            "numberedList",
            "|",
            "undo",
            "redo",
        ],
        # No image button is offered, but the bundled image plugin still warns
        # on every load unless its own toolbar has something in it.
        "image": {"toolbar": ["imageTextAlternative"]},
        "heading": {
            "options": [
                {
                    "model": "paragraph",
                    "title": "Paragrafo",
                    "class": "ck-heading_paragraph",
                },
                {
                    "model": "heading2",
                    "view": "h2",
                    "title": "Titolo di sezione",
                    "class": "ck-heading_heading2",
                },
            ]
        },
    }
}
CKEDITOR_5_USER_LANGUAGE = True
CKEDITOR_5_FILE_UPLOAD_PERMISSION = "staff"

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

# INTAKE
# A draft nobody has touched for this long earns one reminder, never two.
INTAKE_DRAFT_REMINDER_HOURS = env.int("INTAKE_DRAFT_REMINDER_HOURS", default=24)
# ...and is deleted this long after its last change, which is also what the
# privacy notice promises about keeping only what is still needed.
INTAKE_DRAFT_EXPIRY_DAYS = env.int("INTAKE_DRAFT_EXPIRY_DAYS", default=30)

# EVENTS
# A booking nobody confirmed this long after the event is not coming back to
# be confirmed; the application that made it goes with it.
EVENTS_BOOKING_SWEEP_DAYS = env.int("EVENTS_BOOKING_SWEEP_DAYS", default=30)
# The link mailed from the Bookings card has no event to die with, so it says
# how long it lasts itself.
EVENTS_BOOKING_LINK_DAYS = env.int("EVENTS_BOOKING_LINK_DAYS", default=7)
# One link per address per this long: the card is a public form that sends
# mail, which is otherwise a way to flood somebody else's inbox.
EVENTS_BOOKING_LINK_THROTTLE_SECONDS = env.int(
    "EVENTS_BOOKING_LINK_THROTTLE_SECONDS", default=300
)

# PWA
PWA_APP_NAME = "OpenSeat"
PWA_APP_DESCRIPTION = "Event bookings and membership roster for non-profit associations"
PWA_APP_THEME_COLOR = "#ED5C08"
PWA_APP_BACKGROUND_COLOR = "#ffffff"
PWA_APP_DISPLAY = "standalone"
PWA_APP_SCOPE = "/"
PWA_APP_START_URL = "/"
PWA_APP_ORIENTATION = "any"
PWA_APP_LANG = "it-IT"
PWA_APP_ICONS = [{"src": "/static/img/icon-512.png", "sizes": "512x512"}]
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
# Every form allauth builds gets the same daisyUI widget classes as the rest
# of the site — see core.forms.DaisyWidgetsMixin.
ACCOUNT_FORMS = {
    "login": "accounts.forms.LoginForm",
    "signup": "accounts.forms.SignupForm",
    "add_email": "accounts.forms.AddEmailForm",
    "change_password": "accounts.forms.ChangePasswordForm",
    "set_password": "accounts.forms.SetPasswordForm",
    "reset_password": "accounts.forms.ResetPasswordForm",
    "reset_password_from_key": "accounts.forms.ResetPasswordKeyForm",
}

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
# Mail leaves the request cycle, so nothing in it can infer its own host. The
# prod branch re-reads this without a default: a base URL guessed there makes
# every link the association sends out unclickable, and nobody tests their
# own confirmation mail.
SITE_BASE_URL = env("SITE_BASE_URL", default="http://localhost:8000").rstrip("/")

# DBBACKUP. The destination is the "dbbackup" alias of STORAGES; the older
# DBBACKUP_STORAGE / DBBACKUP_STORAGE_OPTIONS pair is read by nothing since
# django-dbbackup 4.2, so setting it would silently back up to the wrong place.
# It stays on local disk unless a bucket is configured below.
DBBACKUP_CLEANUP_KEEP = 10
DBBACKUP_CLEANUP_KEEP_MEDIA = 10
# dbbackup's own cleanup keeps a count, not an age. ops.maintenance answers
# "nothing older than this" on whatever storage the alias points at.
BACKUP_RETENTION_DAYS = env.int("BACKUP_RETENTION_DAYS", default=30)
# An upload lands on disk before its row is saved, so a sweep in between would
# delete a file somebody is still attaching. Spare anything this recent.
MEDIA_ORPHAN_GRACE_HOURS = env.int("MEDIA_ORPHAN_GRACE_HOURS", default=6)

STORAGES["dbbackup"] = {
    "BACKEND": "django.core.files.storage.FileSystemStorage",
    "OPTIONS": {"location": str(BASE_DIR / "backups")},
}
if BACKUP_BUCKET_NAME := env("BACKUP_BUCKET_NAME", default=""):
    # Backups are the one thing worth keeping off the host: a volume dies with
    # the machine it is attached to. Any S3-compatible endpoint will do,
    # a self-hosted MinIO included.
    STORAGES["dbbackup"] = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "bucket_name": BACKUP_BUCKET_NAME,
            "endpoint_url": env("BACKUP_ENDPOINT_URL", default=None),
            "region_name": env("BACKUP_REGION", default="auto"),
            "access_key": env("BACKUP_ACCESS_KEY", default=""),
            "secret_key": env("BACKUP_SECRET_KEY", default=""),
            "default_acl": None,  # R2 and B2 reject per-object ACLs
            "location": env("BACKUP_PREFIX", default="openseat"),
        },
    }

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
    MIDDLEWARE.insert(1, "django_devbar.middleware.DevBarMiddleware")
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
    # Serves STATIC_ROOT and MEDIA_ROOT alike, ahead of LoginRequiredMiddleware
    # so a public page keeps its logo. Uploads are not part of the build, so
    # WhiteNoise must look at the filesystem per request rather than indexing
    # once at boot, or a logo added after the container started stays a 404.
    MIDDLEWARE.insert(1, "core.middleware.MediaWhiteNoiseMiddleware")
    WHITENOISE_AUTOREFRESH = True
    SITE_BASE_URL = env("SITE_BASE_URL").rstrip("/")  # unset must crash at startup
    # The proxy terminates TLS and reaches the app over plain HTTP, so without
    # this request.is_secure() is always False: SECURE_SSL_REDIRECT would then
    # redirect every request to itself forever. Traefik always sets the header.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    # The site answers on one address, and that is the only origin a form may
    # post from — no second variable to keep in step with SITE_BASE_URL.
    CSRF_TRUSTED_ORIGINS = [SITE_BASE_URL]
    DATABASES = {
        "default": dj_database_url.config(
            conn_max_age=env("DATABASE_CONN_MAX_AGE"),
            ssl_require=env("DATABASE_SSL_REQUIRE"),
        )
    }
    STORAGES["staticfiles"] = {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    }
    # A managed Redis is password-protected: Coolify generates one when it
    # provisions the service, and an empty value keeps a bare local instance
    # working unchanged.
    REDIS_HOST = env("REDIS_HOST", default="localhost")
    REDIS_PORT = env.int("REDIS_PORT", default=6379)
    REDIS_PASSWORD = env("REDIS_PASSWORD", default="")
    Q_CLUSTER = {
        **Q_CLUSTER_BASE,
        "redis": {
            "host": REDIS_HOST,
            "port": REDIS_PORT,
            "db": env.int("REDIS_DB", default=0),
            "password": REDIS_PASSWORD or None,
        },
    }
    # The throttle has to be shared: in local memory each granian worker keeps
    # its own count, so the real limit would be one send per worker.
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": "redis://:{}@{}:{}/{}".format(
                quote(REDIS_PASSWORD, safe=""),
                REDIS_HOST,
                REDIS_PORT,
                env.int("REDIS_CACHE_DB", default=1),
            ),
        }
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
