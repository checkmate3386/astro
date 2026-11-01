"""Chargement et validation du fichier events.json, relu à chaque appel."""
import json
from pathlib import Path

from django.conf import settings
from django.utils.text import slugify


class EventConfigurationError(ValueError):
    """Signale une configuration d'événements absente ou invalide."""


EVENTS_FILE = Path(settings.BASE_DIR) / "events.json"


def load_events():
    try:
        with EVENTS_FILE.open(encoding="utf-8") as event_file:
            data = json.load(event_file)
    except FileNotFoundError as error:
        raise EventConfigurationError(
            f"Le fichier des événements est introuvable : {EVENTS_FILE}"
        ) from error
    except json.JSONDecodeError as error:
        raise EventConfigurationError(
            f"JSON invalide dans {EVENTS_FILE}, ligne {error.lineno}, "
            f"colonne {error.colno} : {error.msg}"
        ) from error
    except OSError as error:
        raise EventConfigurationError(
            f"Impossible de lire le fichier des événements {EVENTS_FILE} : {error}"
        ) from error

    if not isinstance(data, list):
        raise EventConfigurationError(
            f"{EVENTS_FILE} doit contenir une liste d'événements."
        )

    events = []
    seen_ids = set()
    seen_slugs = set()
    required = {"id", "titre", "description", "details", "limite"}

    for index, event in enumerate(data, start=1):
        label = f"Événement n° {index}"
        if not isinstance(event, dict):
            raise EventConfigurationError(f"{label} doit être un objet JSON.")
        missing = required - event.keys()
        if missing:
            raise EventConfigurationError(
                f"{label} : champs requis manquants : {', '.join(sorted(missing))}."
            )

        event_id = event["id"]
        if isinstance(event_id, bool) or not isinstance(event_id, (int, str)):
            raise EventConfigurationError(
                f"{label} : « id » doit être un entier ou un texte non vide."
            )
        event_key = str(event_id).strip()
        if not event_key:
            raise EventConfigurationError(f"{label} : « id » ne peut pas être vide.")
        if event_key in seen_ids:
            raise EventConfigurationError(
                f"{label} : l'identifiant « {event_key} » est utilisé plusieurs fois."
            )
        seen_ids.add(event_key)

        title = event["titre"]
        description = event["description"]
        details = event["details"]
        limit = event["limite"]
        if not isinstance(title, str) or not title.strip():
            raise EventConfigurationError(f"{label} : « titre » doit être un texte non vide.")
        if not isinstance(description, str) or not description.strip():
            raise EventConfigurationError(
                f"{label} : « description » doit être un texte non vide."
            )
        if not isinstance(details, list) or not all(
            isinstance(item, str) for item in details
        ):
            raise EventConfigurationError(
                f"{label} : « details » doit être une liste de textes."
            )
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise EventConfigurationError(
                f"{label} : « limite » doit être un entier positif."
            )

        event_slug = slugify(title)
        if not event_slug:
            raise EventConfigurationError(
                f"{label} : le titre doit produire un slug d'URL non vide."
            )
        if event_slug in seen_slugs:
            raise EventConfigurationError(
                f"{label} : le titre produit un slug déjà utilisé (« {event_slug} »)."
            )
        seen_slugs.add(event_slug)
        events.append(
            {
                "event_id": event_key,
                "slug": event_slug,
                "titre": title.strip(),
                "description": description.strip(),
                "details": details,
                "limite": limit,
            }
        )

    return events


def get_event_by_slug(event_slug):
    return next(
        (event for event in load_events() if event["slug"] == event_slug),
        None,
    )
