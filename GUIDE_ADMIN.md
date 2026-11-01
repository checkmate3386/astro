# Guide d’utilisation de l’administration

## 1. Créer le compte administrateur

Dans le terminal du projet, activez l’environnement virtuel puis exécutez :

```bash
python manage.py createsuperuser
```

Choisissez un nom d’utilisateur et un mot de passe robuste. Le mot de passe
n’est jamais enregistré dans le dépôt. Chaque personne ayant besoin de l’accès
administrateur doit disposer de son propre compte.

## 2. Se connecter

Ouvrez `https://votre-domaine/gestion-astronomie/` (ou la valeur définie par
`ADMIN_URL`) et connectez-vous. Le chemin par défaut n’est pas `/admin/`.
L’adresse peut être modifiée dans l’environnement, par exemple :

```text
ADMIN_URL=espace-prive/
```

Après un changement de chemin, rechargez l’application web et utilisez
`/espace-prive/`.

## 3. Lire et filtrer les inscriptions

Dans **Inscriptions aux soirées**, la liste présente la soirée, l’adresse
e-mail, le nombre de personnes et les dates de création/modification. Le filtre
**Soirée** présente les titres chargés depuis `events.json`. Les inscriptions
liées à une soirée retirée du JSON restent disponibles sous **Anciennes
soirées**. La recherche porte sur l’adresse e-mail, le nom et le prénom.

Ouvrez une inscription pour consulter ou corriger les participants et les
informations de matériel. Les IDs internes des événements ne sont pas affichés.
Les modifications d’événements se font dans `events.json`, jamais dans
l’administration.

## 4. Exporter un fichier CSV

Dans la liste des inscriptions :

1. Cochez les inscriptions à exporter (ou cochez la case d’en-tête pour la page).
2. Choisissez **Exporter les inscriptions sélectionnées en CSV** dans la liste
   des actions.
3. Cliquez sur **Exécuter**.

Le fichier contient une ligne par participant et les colonnes soirée, e-mail,
matériel, identité du participant, statut mineur, âge et dates. Les champs sont
protégés contre l’interprétation involontaire comme formule de tableur.

## 5. Données et confidentialité

Les données de mineurs sont limitées au nom, au prénom et à l’âge. Les
inscriptions ne sont pas supprimées si une soirée disparaît de `events.json`.
Manipulez les exports avec précaution et supprimez-les lorsqu’ils ne sont plus
nécessaires. Les données du site servent uniquement à l’organisation des
soirées.
