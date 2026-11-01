"""Vues publiques des événements et des inscriptions."""
import hashlib
import mimetypes
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import SuspiciousFileOperation
from django.db import IntegrityError, transaction
from django.db.models import F
from django.http import FileResponse, Http404, HttpResponse, HttpResponseNotAllowed
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils._os import safe_join
from django.views.decorators.http import require_GET, require_http_methods

from .events import get_event_by_slug, load_events
from .forms import RegistrationForm
from .models import CapacityMutex, EmailLookupAttempt, Participant, Registration


def _event_or_404(slug):
    event = get_event_by_slug(slug)
    if event is None:
        raise Http404("Cette soirée n’existe plus.")
    return event


def _lock_registration_capacity():
    updated = CapacityMutex.objects.filter(pk=1).update(version=F("version") + 1)
    if not updated:
        raise RuntimeError(
            "Verrou de capacité absent ; exécutez les migrations Django."
        )


def _registration_context(event, registration=None, form=None, active_tab="signup"):
    registered_people = (
        Participant.objects.filter(registration__event_id=event["event_id"]).count()
    )
    form = form or RegistrationForm()
    signup_form = form if active_tab == "signup" else RegistrationForm()
    return {
        "event": event,
        "remaining_places": max(0, event["limite"] - registered_people),
        "form": form,
        "signup_form": signup_form,
        "participant_rows": [
            {
                "first_name": form[f"first_name_{index}"],
                "last_name": form[f"last_name_{index}"],
                "is_minor": form[f"is_minor_{index}"],
                "age": form[f"age_{index}"],
            }
            for index in range(6)
        ],
        "registration": registration,
        "active_tab": active_tab,
    }


def home(request):
    return render(request, "inscriptions/home.html", {"events": load_events()})


def _lookup_is_limited(request):
    client_ip = request.META.get("REMOTE_ADDR", "unknown")
    ip_hash = hashlib.sha256(client_ip.encode("utf-8")).hexdigest()
    now = timezone.now()
    window = timedelta(seconds=settings.EMAIL_LOOKUP_WINDOW_SECONDS)

    with transaction.atomic():
        attempt, created = EmailLookupAttempt.objects.select_for_update().get_or_create(
            ip_hash=ip_hash,
            defaults={"window_started_at": now, "attempts": 0},
        )
        if not created and now - attempt.window_started_at >= window:
            attempt.window_started_at = now
            attempt.attempts = 0
        if attempt.attempts >= settings.EMAIL_LOOKUP_LIMIT:
            attempt.save(update_fields=("window_started_at", "attempts"))
            return True
        attempt.attempts += 1
        attempt.save(update_fields=("window_started_at", "attempts"))
    return False


def _make_initial(registration):
    participants = [
        {
            "first_name": participant.first_name,
            "last_name": participant.last_name,
            "is_minor": participant.is_minor,
            "age": participant.age,
        }
        for participant in registration.participants.all()
    ]
    return {
        "email": registration.email,
        "email_confirm": registration.email,
        "people_count": str(len(participants)),
        "brings_equipment": registration.brings_equipment,
        "equipment_description": registration.equipment_description,
    }, participants


def _save_participants(registration, form):
    registration.participants.all().delete()
    Participant.objects.bulk_create(
        [
            Participant(registration=registration, **participant)
            for participant in form.cleaned_data["participants"]
        ]
    )


@require_http_methods(["GET", "POST"])
def event_detail(request, slug):
    event = _event_or_404(slug)
    if request.method == "GET":
        return render(
            request,
            "inscriptions/event_detail.html",
            _registration_context(event),
        )

    action = request.POST.get("action", "")
    if action == "signup":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            requested_count = len(form.cleaned_data["participants"])
            try:
                with transaction.atomic():
                    _lock_registration_capacity()
                    registered_people = Participant.objects.filter(
                        registration__event_id=event["event_id"]
                    ).count()
                    remaining = max(0, event["limite"] - registered_people)
                    if requested_count > remaining:
                        message = (
                            "Il n’y a plus de place disponible."
                            if remaining == 0
                            else f"Il ne reste que {remaining} place(s) pour cette soirée."
                        )
                        form.add_error(None, message)
                    elif Registration.objects.filter(
                        event_id=event["event_id"],
                        email=form.cleaned_data["email"],
                    ).exists():
                        form.add_error(
                            "email",
                            "Une inscription existe déjà pour cette adresse. "
                            "Utilisez « Modifier mon inscription ».",
                        )
                    else:
                        registration = Registration.objects.create(
                            event_id=event["event_id"],
                            email=form.cleaned_data["email"],
                            brings_equipment=form.cleaned_data["brings_equipment"],
                            equipment_description=form.cleaned_data[
                                "equipment_description"
                            ],
                        )
                        _save_participants(registration, form)
            except IntegrityError:
                form.add_error(
                    "email",
                    "Une inscription existe déjà pour cette adresse.",
                )
            if not form.errors:
                messages.success(request, "Votre inscription est confirmée.")
                return redirect("event-detail", slug=slug)
        return render(
            request,
            "inscriptions/event_detail.html",
            _registration_context(event, form=form, active_tab="signup"),
        )

    if action == "lookup":
        if _lookup_is_limited(request):
            messages.error(
                request,
                "Trop de tentatives. Veuillez réessayer dans quelques minutes.",
            )
            return redirect("event-detail", slug=slug)
        email = request.POST.get("email", "").strip().lower()
        registration = Registration.objects.filter(
            event_id=event["event_id"],
            email=email,
        ).first()
        messages.info(
            request,
            "Si une inscription correspond à cette adresse, "
            "son formulaire est affiché ci-dessous.",
        )
        if registration is not None:
            initial, participants = _make_initial(registration)
            form = RegistrationForm(initial=initial, participants=participants)
        else:
            form = None
        return render(
            request,
            "inscriptions/event_detail.html",
            _registration_context(
                event,
                registration=registration,
                form=form,
                active_tab="modify",
            ),
        )

    if action == "update":
        original_email = request.POST.get("original_email", "").strip().lower()
        registration = Registration.objects.filter(
            event_id=event["event_id"],
            email=original_email,
        ).first()
        if registration is None:
            messages.info(
                request,
                "Si une inscription correspond à cette adresse, "
                "son formulaire est affiché ci-dessous.",
            )
            return redirect("event-detail", slug=slug)

        form = RegistrationForm(request.POST)
        if form.is_valid():
            registration_missing = False
            with transaction.atomic():
                _lock_registration_capacity()
                current_registration = Registration.objects.filter(
                    pk=registration.pk,
                    event_id=event["event_id"],
                ).first()
                if current_registration is None:
                    registration_missing = True
                else:
                    old_count = current_registration.participants.count()
                    new_count = len(form.cleaned_data["participants"])
                    other_people = (
                        Participant.objects.filter(
                            registration__event_id=event["event_id"]
                        )
                        .exclude(registration=current_registration)
                        .count()
                    )
                    if (
                        new_count > old_count
                        and other_people + new_count > event["limite"]
                    ):
                        remaining = max(
                            0,
                            event["limite"] - other_people - old_count,
                        )
                        form.add_error(
                            None,
                            "Cette modification dépasserait la capacité de la soirée. "
                            f"Vous pouvez ajouter au maximum {remaining} personne(s).",
                        )

                    email_in_use = Registration.objects.filter(
                        event_id=event["event_id"],
                        email=form.cleaned_data["email"],
                    ).exclude(pk=current_registration.pk).exists()
                    if email_in_use:
                        form.add_error(
                            "email",
                            "Cette adresse est déjà utilisée pour cette soirée.",
                        )

                    if not form.errors:
                        current_registration.email = form.cleaned_data["email"]
                        current_registration.brings_equipment = form.cleaned_data[
                            "brings_equipment"
                        ]
                        current_registration.equipment_description = form.cleaned_data[
                            "equipment_description"
                        ]
                        current_registration.save()
                        _save_participants(current_registration, form)
                        registration = current_registration
            if registration_missing:
                messages.info(
                    request,
                    "Si une inscription correspond à cette adresse, "
                    "son formulaire est affiché ci-dessous.",
                )
                return redirect("event-detail", slug=slug)
            if not form.errors:
                messages.success(request, "Votre inscription a été mise à jour.")
                return redirect("event-detail", slug=slug)
        return render(
            request,
            "inscriptions/event_detail.html",
            _registration_context(
                event,
                registration=registration,
                form=form,
                active_tab="modify",
            ),
        )

    if action == "delete":
        email = request.POST.get("original_email", "").strip().lower()
        with transaction.atomic():
            _lock_registration_capacity()
            registration = Registration.objects.filter(
                event_id=event["event_id"],
                email=email,
            ).first()
            if registration is not None:
                registration.delete()
        if registration is not None:
            messages.success(request, "Votre inscription a été supprimée.")
        else:
            messages.info(
                request,
                "Si une inscription correspond à cette adresse, "
                "elle a été prise en compte.",
            )
        return redirect("event-detail", slug=slug)

    return HttpResponseNotAllowed(["GET", "POST"])


@require_GET
def robots_txt(request):
    return HttpResponse(
        "User-agent: *\nDisallow: /\n",
        content_type="text/plain; charset=utf-8",
    )


@require_http_methods(["GET", "HEAD"])
def static_asset(request, path):
    """Sert uniquement les fichiers collectés, à travers le middleware Django."""
    try:
        static_root = Path(settings.STATIC_ROOT).resolve()
        asset_path = Path(safe_join(static_root, path)).resolve(strict=True)
    except (OSError, ValueError, SuspiciousFileOperation):
        raise Http404("Fichier statique introuvable.") from None
    if not asset_path.is_relative_to(static_root) or not asset_path.is_file():
        raise Http404("Fichier statique introuvable.")

    content_type = mimetypes.guess_type(asset_path.name)[0] or "application/octet-stream"
    if request.method == "HEAD":
        return HttpResponse(content_type=content_type)
    return FileResponse(asset_path.open("rb"), content_type=content_type)
