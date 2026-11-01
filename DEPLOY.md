# Déploiement sur PythonAnywhere

Cette application utilise Django et SQLite, ne requiert aucun serveur de mail
et n'envoie aucun e-mail. La base `db.sqlite3` doit rester dans le répertoire
persistant de votre compte PythonAnywhere ; ne la stockez ni dans Git ni dans
un répertoire temporaire.

Les étapes ci-dessous supposent que le dépôt GitHub existe déjà et que vous
connaissez le nom de votre compte PythonAnywhere et le nom du dépôt.

## 1. Créer l'application PythonAnywhere

1. Connectez-vous à PythonAnywhere et ouvrez l'onglet **Web**.
2. Cliquez **Add a new web app** et choisissez votre domaine
   `VOTRE_COMPTE.pythonanywhere.com`.
3. Choisissez **Manual configuration** (ne choisissez pas le générateur
   Django, car le projet existe déjà dans le dépôt).
4. Choisissez Python **3.10 ou plus récent**. La version sélectionnée ici doit
   être la même que celle qui servira à créer l'environnement virtuel.
5. Attendez la création de l'application ; la page Web affichera les champs
   pour le code, l'environnement virtuel et le fichier WSGI.

## 2. Cloner le dépôt

Dans **Consoles**, ouvrez une console **Bash**. Remplacez les deux valeurs
d'exemple par celles de votre dépôt :

```bash
cd ~
git clone https://github.com/VOTRE_COMPTE/VOTRE_DEPOT.git astro
cd ~/astro
```

Le code sera dans `/home/VOTRE_COMPTE/astro`. Utilisez ce chemin complet dans
les réglages Web ci-dessous. Si le dépôt est privé, configurez l'accès GitHub
depuis votre compte PythonAnywhere ; n'inscrivez jamais de jeton ou de mot de
passe dans l'URL de clonage ou dans un fichier versionné.

## 3. Créer l'environnement Python et installer Django

Dans la console Bash, vérifiez quelle version Python 3.10+ est disponible dans
votre compte PythonAnywhere. L'exemple utilise Python 3.11 :

```bash
mkvirtualenv --python=/usr/bin/python3.11 astro-venv
workon astro-venv
cd ~/astro
python --version
pip install -r requirements.txt
```

Si vous avez choisi une autre version dans l'onglet **Web**, remplacez
`python3.11` par son chemin disponible (par exemple `python3.12`). Dans
**Web → Virtualenv**, indiquez :

```text
/home/VOTRE_COMPTE/.virtualenvs/astro-venv
```

L'installation actuelle n'ajoute que Django ; l'application n'a pas besoin
d'un service d'e-mail ni d'une base de données externe.

## 4. Indiquer le répertoire du projet

Dans **Web → Code** :

- **Source code** : `/home/VOTRE_COMPTE/astro`
- **Working directory** : `/home/VOTRE_COMPTE/astro`
- **WSGI configuration file** : ouvrez le chemin affiché par PythonAnywhere,
  généralement `/var/www/VOTRE_COMPTE_pythonanywhere_com_wsgi.py`

Remplacez `VOTRE_COMPTE` par votre véritable identifiant PythonAnywhere. Ne
commitez pas ce fichier WSGI : il se trouve normalement dans `/var/www`, hors
du dépôt.

## 5. Configurer WSGI et les variables de production

Générez une clé secrète dans la console Bash, après `workon astro-venv` :

```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

Copiez la valeur obtenue dans le fichier WSGI privé, sans la publier et sans
réutiliser la clé de développement. Dans le fichier WSGI, remplacez le bloc
généré par PythonAnywhere par la configuration suivante :

```python
import os
import sys

project = "/home/VOTRE_COMPTE/astro"
if project not in sys.path:
    sys.path.insert(0, project)

os.environ["SECRET_KEY"] = "COLLER-ICI-LA-CLE-ALEATOIRE"
os.environ["DEBUG"] = "False"
os.environ["ALLOWED_HOSTS"] = "VOTRE_COMPTE.pythonanywhere.com"
os.environ["ADMIN_URL"] = "chemin-prive-aleatoire/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
```

Remplacez :

- `VOTRE_COMPTE` par votre identifiant PythonAnywhere ;
- `SECRET_KEY` par la valeur générée ;
- `ADMIN_URL` par un chemin difficile à deviner, sans `/` initial (par exemple
  `espace-club-7f3a/`). Le chemin par défaut, si cette variable n'est pas
  définie, est `gestion-astronomie/`.

`DEBUG=False` est impératif en production. `ALLOWED_HOSTS` doit contenir le nom
d'hôte exact, sans `https://`, chemin ou slash final. Si vous servez aussi un
domaine personnalisé, ajoutez-le à la liste en le séparant par une virgule.
Le fichier `.env.example` du dépôt est un modèle sans secret : Django ne le
charge pas automatiquement. Sur PythonAnywhere, définir ces valeurs dans le
fichier WSGI privé suffit ; aucune dépendance dotenv n'est installée.

## 6. Créer les tables SQLite et le compte admin

Dans la console Bash :

```bash
workon astro-venv
cd ~/astro
python manage.py migrate
python manage.py createsuperuser
```

`migrate` crée `~/astro/db.sqlite3` sur le stockage persistant. Créez un
utilisateur admin distinct et choisissez un mot de passe solide. L'interface
admin sera disponible à :

```text
https://VOTRE_COMPTE.pythonanywhere.com/chemin-prive-aleatoire/
```

Consultez [GUIDE_ADMIN.md](GUIDE_ADMIN.md) pour gérer les inscriptions et
télécharger un export CSV.

## 7. Collecter les fichiers statiques

Dans la console Bash :

```bash
cd ~/astro
python manage.py collectstatic --noinput
```

Par défaut, ne créez pas de mapping `/static/` dans **Web → Static files**.
Cette application sert les fichiers collectés par Django pour que le
middleware ajoute aussi `X-Robots-Tag` aux réponses statiques et aux erreurs.
Le serveur statique Django convient à une petite activité, mais est moins
performant qu'un serveur frontal.

Si vous configurez plutôt PythonAnywhere pour servir directement `/static/`
depuis `/home/VOTRE_COMPTE/astro/staticfiles/`, le serveur frontal contournera
le middleware Django. Il faut alors configurer également l'en-tête
`X-Robots-Tag: noindex, nofollow, noarchive, nosnippet, noimageindex` sur toutes
les réponses statiques, y compris les erreurs. Sinon, laissez les fichiers
statiques passer par Django.

## 8. Vérifier puis recharger le site

Avant le rechargement, vous pouvez contrôler la configuration depuis la
console :

```bash
cd ~/astro
python manage.py check
python manage.py test
```

Dans **Web**, cliquez **Reload**. Visitez ensuite :

- `https://VOTRE_COMPTE.pythonanywhere.com/` : page d'accueil ;
- `https://VOTRE_COMPTE.pythonanywhere.com/robots.txt` : doit afficher
  `User-agent: *` et `Disallow: /` ;
- l'URL de l'administration définie par `ADMIN_URL` ;
- une page d'événement et une inscription de test.

Vous pouvez vérifier l'en-tête de robots depuis une console disposant de curl :

```bash
curl -I https://VOTRE_COMPTE.pythonanywhere.com/
curl -I https://VOTRE_COMPTE.pythonanywhere.com/static/css/site.css
```

Les réponses doivent inclure :

```text
X-Robots-Tag: noindex, nofollow, noarchive, nosnippet, noimageindex
```

N'activez pas de mapping statique PythonAnywhere si cette seconde réponse ne
contient pas l'en-tête.

## 9. Déployer une mise à jour ultérieure

Depuis la console Bash :

```bash
cd ~/astro
git pull
workon astro-venv
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

Dans **Web**, cliquez ensuite **Reload**. `migrate` est sans risque à répéter :
il n'applique que les nouvelles migrations. Les modifications de
`events.json` prennent effet sans migration ; les nouvelles pages et entrées
de menu sont disponibles dès que le fichier est mis à jour.

Avant chaque mise à jour importante, sauvegardez `db.sqlite3` hors du dépôt et
vérifiez que `git status` ne signale pas de modifications locales que `git pull`
pourrait empêcher d'intégrer.

## Versionnage et sécurité

- Le dépôt doit contenir le code, `events.json`, les migrations et
  `.env.example`, mais pas de secret réel.
- `.gitignore` exclut les fichiers `.env` (tout en conservant
  `.env.example`), `db.sqlite3` et ses fichiers de journal, les caches
  `__pycache__`, `.venv`, `staticfiles` et les exports CSV.
- Vérifiez avant un commit avec `git status --short` et `git ls-files`. Ajouter
  une règle à `.gitignore` ne retire pas un fichier déjà suivi ; s'il y en a
  un, retirez-le de l'index avec `git rm --cached NOM_DU_FICHIER`, puis
  vérifiez qu'il ne contient pas déjà de données sensibles dans l'historique.
- Gardez `DEBUG=False`, protégez le fichier WSGI qui contient `SECRET_KEY`,
  utilisez HTTPS et limitez `ALLOWED_HOSTS`.
- SQLite est stockée sur le disque persistant du compte. Sauvegardez-la
  régulièrement et ne la déplacez pas vers un répertoire temporaire.
- Les données de mineurs doivent rester limitées au nom, prénom et âge. Ne
  partagez pas les exports d'inscriptions et supprimez-les lorsqu'ils ne sont
  plus nécessaires.
