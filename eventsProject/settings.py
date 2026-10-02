"""
Configuration du projet eventsProject.

Les valeurs sensibles (SECRET_KEY, DEBUG, ALLOWED_HOSTS) sont lues depuis des
variables d'environnement. Des valeurs par défaut sont prévues pour le
développement local uniquement.

Documentation : https://docs.djangoproject.com/fr/5.2/ref/settings/
"""

import os
from pathlib import Path

# Dossier racine du projet (celui qui contient manage.py).
BASE_DIR = Path(__file__).resolve().parent.parent


# --- Sécurité ---------------------------------------------------------------
# En production, définir les variables d'environnement DJANGO_SECRET_KEY,
# DJANGO_DEBUG=False et DJANGO_ALLOWED_HOSTS.

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-cle-de-developpement-uniquement-a-changer-en-production",
)

DEBUG = os.environ.get("DJANGO_DEBUG", "True") == "True"

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")


# --- Applications -----------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Applications du projet
    "events.apps.EventsConfig",  # événements, catégories, inscriptions
    "accounts.apps.AccountsConfig",  # connexion, déconnexion, création de compte
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "eventsProject.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # Templates globaux partagés par toutes les applications (base.html...)
        "DIRS": [BASE_DIR / "templates"],
        # Templates propres à chaque application (events/templates/events/...)
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "eventsProject.wsgi.application"


# --- Base de données --------------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# --- Mots de passe ----------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# --- Authentification -------------------------------------------------------

LOGIN_URL = "accounts:login"  # page affichée par @login_required
LOGIN_REDIRECT_URL = "events:liste"  # après la connexion
LOGOUT_REDIRECT_URL = "events:liste"  # après la déconnexion


# --- Langue et fuseau horaire ----------------------------------------------

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Africa/Casablanca"
USE_I18N = True
USE_TZ = True


# --- Fichiers statiques (CSS) -----------------------------------------------

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
