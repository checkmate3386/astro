# Déploiement sur PythonAnywhere

Ce guide utilise SQLite et ne requiert aucun service externe ni envoi de mail.
`db.sqlite3` doit rester sur le stockage persistant de votre compte PythonAnywhere.

## 1. Récupérer le projet

Dans une console Bash PythonAnywhere, choisissez le répertoire de déploiement :

```bash
cd ~
git clone https://github.com/VOTRE-COMPTE/VOTRE-DEPOT.git astro
cd ~/astro
```

Pour une mise à jour ultérieure :

```bash
cd ~/astro
git pull
```

Ne placez pas la base SQLite dans un répertoire temporaire ou partagé entre
comptes. Gardez une copie de sauvegarde hors du dépôt avant les mises à jour
importantes.

## 2. Créer l’environnement virtuel

Utilisez une version Python disponible sur votre compte (exemple Python 3.11) :

```bash
mkvirtualenv --python=/usr/bin/python3.11 astro-venv
workon astro-venv
cd ~/astro
pip install -r requirements.txt
```

Dans l’onglet **Web**, renseignez le chemin de cet environnement virtuel. À
chaque déploiement qui modifie `requirements.txt`, réactivez-le et relancez
`pip install -r requirements.txt`.

## 3. Configurer les variables d’environnement et WSGI

Dans **Web → Code**, indiquez le fichier WSGI associé à l’application, par
exemple `/var/www/VOTRE_COMPTE_pythonanywhere_com_wsgi.py`. Modifiez ce fichier
pour charger les variables avant Django :

```python
import os
import sys

project = "/home/VOTRE_COMPTE/astro"
if project not in sys.path:
    sys.path.insert(0, project)

os.environ["SECRET_KEY"] = "COLLER-ICI-UNE-CLE-ALEATOIRE-LONGUE"
os.environ["DEBUG"] = "False"
os.environ["ALLOWED_HOSTS"] = "VOTRE_COMPTE.pythonanywhere.com"
os.environ["ADMIN_URL"] = "chemin-prive-aleatoire/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
```

Générez une clé aléatoire localement avec `python -c "from
django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
dans l’environnement virtuel. Ne partagez pas la clé, ne la mettez pas dans
Git et n’utilisez pas la clé de développement du fichier `settings.py`.
`ALLOWED_HOSTS` doit contenir exactement le nom d’hôte du site, sans schéma ni
chemin. Vous pouvez ajouter plusieurs hôtes en les séparant par des virgules.

Les valeurs du WSGI sont les variables d’environnement du processus. Si vous
préférez un fichier `.env`, ne le commitez jamais : il faut charger explicitement
ce fichier dans WSGI (aucune dépendance dotenv n’est installée).

## 4. Créer/mettre à jour SQLite et l’administrateur

Dans une console avec l’environnement activé :

```bash
cd ~/astro
python manage.py migrate
python manage.py createsuperuser
```

`migrate` crée le fichier persistant `~/astro/db.sqlite3` et les tables, y
compris le compteur de tentatives de recherche. Pour une mise à jour, refaites
`git pull`, puis `python manage.py migrate`. Les événements ne nécessitent
aucune migration.

## 5. Collecter les fichiers statiques et recharger

```bash
python manage.py collectstatic --noinput
```

Par défaut, ne configurez pas de mapping statique `/static/` dans **Web →
Static files** : les fichiers collectés sont servis par la route Django, de
façon à recevoir le même en-tête anti-indexation que les pages et les erreurs.
Ce mode est moins performant que le serveur statique du frontal. Si vous
choisissez plutôt de faire servir `/static/` directement depuis
`/home/VOTRE_COMPTE/astro/staticfiles/`, le serveur statique doit lui aussi
ajouter `X-Robots-Tag: noindex, nofollow, noarchive, nosnippet, noimageindex`
à toutes ses réponses, y compris les erreurs ; sinon, conservez le mode Django.

Cliquez ensuite sur **Reload** dans l’onglet **Web**. Vérifiez la page d’accueil,
`/robots.txt`, l’en-tête `X-Robots-Tag`, les fichiers CSS/JavaScript et l’URL
d’administration.

## 6. Mises à jour courantes

```bash
cd ~/astro
git pull
workon astro-venv
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

Puis rechargez l’application web. Avant un `git pull`, vérifiez que les
modifications locales sont sauvegardées. `events.json` est chargé à chaque
requête : ses ajouts et suppressions prennent effet après la mise à jour, sans
redémarrage ni migration.

## Sécurité et limites

- Gardez `DEBUG=False`, une clé secrète privée et une liste `ALLOWED_HOSTS`
  restrictive en production.
- N’ajoutez pas `db.sqlite3`, `.env`, les exports CSV ou les données
  d’inscription à Git.
- Utilisez HTTPS et un chemin d’administration difficile à deviner.
- SQLite convient à un club à trafic modéré. Faites régulièrement une
  sauvegarde cohérente de la base.
- Le middleware ajoute le marqueur anti-indexation aux réponses Django, y
  compris pages d’erreur et route de fichiers statiques Django. Les fichiers
  servis directement par un serveur statique nécessitent aussi une règle
  d’en-tête sur ce serveur.
