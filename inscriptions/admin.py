import csv

from django.contrib import admin
from django.http import HttpResponse

from .events import load_events
from .models import EmailLookupAttempt, Participant, Registration


def event_title_for_id(event_id):
    event = next(
        (item for item in load_events() if item["event_id"] == event_id),
        None,
    )
    return event["titre"] if event else "Ancienne soirée"


class EventFilter(admin.SimpleListFilter):
    title = "soirée"
    parameter_name = "event"

    def lookups(self, request, model_admin):
        events = load_events()
        choices = [(f"event-{event['slug']}", event["titre"]) for event in events]
        active_ids = [event["event_id"] for event in events]
        has_archived = Registration.objects.exclude(event_id__in=active_ids).exists()
        if has_archived:
            choices.append(("__archived__", "Anciennes soirées"))
        return choices

    def queryset(self, request, queryset):
        selected = self.value()
        if not selected:
            return queryset
        events = load_events()
        if selected == "__archived__":
            active_ids = [event["event_id"] for event in events]
            return queryset.exclude(event_id__in=active_ids)
        slug = selected.removeprefix("event-")
        event = next((item for item in events if item["slug"] == slug), None)
        if event is None:
            return queryset.none()
        return queryset.filter(event_id=event["event_id"])


class ParticipantInline(admin.TabularInline):
    model = Participant
    extra = 0


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ("event_title", "email", "participant_count", "created_at", "updated_at")
    list_filter = (EventFilter, "brings_equipment")
    search_fields = ("email", "participants__first_name", "participants__last_name")
    readonly_fields = ("event_title", "created_at", "updated_at")
    fieldsets = (
        ("Soirée et contact", {"fields": ("event_title", "email")}),
        ("Matériel", {"fields": ("brings_equipment", "equipment_description")}),
        ("Dates", {"fields": ("created_at", "updated_at")}),
    )
    inlines = (ParticipantInline,)
    actions = ("export_registrations_csv",)

    @admin.display(description="Soirée", ordering="event_id")
    def event_title(self, obj):
        return event_title_for_id(obj.event_id)

    @admin.display(description="Personnes")
    def participant_count(self, obj):
        return obj.participants.count()

    @admin.action(description="Exporter les inscriptions sélectionnées en CSV")
    def export_registrations_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="inscriptions.csv"'
        response.write("\ufeff")
        writer = csv.writer(response)
        writer.writerow(
            [
                "Soirée",
                "E-mail",
                "Matériel astro",
                "Description du matériel",
                "Nom",
                "Prénom",
                "Mineur",
                "Âge",
                "Créée le",
                "Modifiée le",
            ]
        )
        for registration in queryset.prefetch_related("participants"):
            participants = list(registration.participants.all()) or [None]
            for participant in participants:
                row = [
                    event_title_for_id(registration.event_id),
                    registration.email,
                    "Oui" if registration.brings_equipment else "Non",
                    registration.equipment_description,
                    participant.last_name if participant else "",
                    participant.first_name if participant else "",
                    (
                        "Oui"
                        if participant and participant.is_minor
                        else "Non" if participant else ""
                    ),
                    participant.age if participant and participant.age else "",
                    registration.created_at.isoformat(),
                    registration.updated_at.isoformat(),
                ]
                writer.writerow([_spreadsheet_safe(value) for value in row])
        return response


def _spreadsheet_safe(value):
    text = str(value)
    if text.startswith(("=", "+", "-", "@", "\t", "\r")):
        return f"'{text}"
    return text


@admin.register(EmailLookupAttempt)
class EmailLookupAttemptAdmin(admin.ModelAdmin):
    list_display = ("window_started_at", "attempts")
    readonly_fields = ("ip_hash", "window_started_at", "attempts")
    ordering = ("-window_started_at",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
