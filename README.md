# Inscriptions aux soirées du club d’astronomie

Site Django classique, dynamique et sans envoi d’e-mail. Le fichier `events.json`
est la source de vérité des soirées ; il est relu à chaque requête. Les données
d’inscription sont conservées dans `db.sqlite3`.

## Lancer en local

Python 3.10+ et pip sont nécessaires.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Le site est disponible sur <http://127.0.0.1:8000/>. La configuration locale
utilise `DEBUG=True` et les hôtes `localhost,127.0.0.1` par défaut.

Pour ajouter ou retirer une soirée, modifiez `events.json` sans migration ni
redémarrage. Chaque événement doit avoir un identifiant unique, un titre unique
après génération du slug, une description, une liste `details` et une limite
positive. Les pages sont accessibles sous `/soirees/<slug-du-titre>/` ; les IDs
ne sont ni affichés ni utilisés dans les URL.

## Administration

L’administration est disponible à l’adresse configurée par `ADMIN_URL` (par
défaut `/gestion-astronomie/`). Consultez le [guide de l’administration](GUIDE_ADMIN.md)
pour créer un compte, gérer les inscriptions et exporter les données en CSV.

## Tests

```bash
python manage.py test
```

## Déploiement

Suivez le [guide pas à pas PythonAnywhere](DEPLOY.md). En production, définissez
au minimum `SECRET_KEY`, `DEBUG=False` et `ALLOWED_HOSTS` dans l’environnement
WSGI. Ne versionnez jamais le fichier `.env` ou `db.sqlite3`.
