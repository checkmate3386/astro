from django.db import models


class CapacityMutex(models.Model):
    """Ligne unique pour sérialiser les modifications de capacité avec SQLite."""

    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    version = models.PositiveBigIntegerField(default=0)

    class Meta:
        verbose_name = "verrou de capacité"
        verbose_name_plural = "verrou de capacité"


class Registration(models.Model):
    event_id = models.CharField(max_length=100)
    email = models.EmailField()
    brings_equipment = models.BooleanField(default=False, verbose_name="Matériel astro")
    equipment_description = models.TextField(
        blank=True, verbose_name="Matériel apporté"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créée le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifiée le")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("event_id", "email"),
                name="unique_registration_per_event_email",
            )
        ]
        ordering = ("event_id", "email")
        verbose_name = "inscription"
        verbose_name_plural = "inscriptions"

    def __str__(self):
        return f"{self.email} — événement"


class Participant(models.Model):
    registration = models.ForeignKey(
        Registration,
        on_delete=models.CASCADE,
        related_name="participants",
        verbose_name="Inscription",
    )
    last_name = models.CharField(max_length=100, verbose_name="Nom")
    first_name = models.CharField(max_length=100, verbose_name="Prénom")
    is_minor = models.BooleanField(default=False, verbose_name="Mineur")
    age = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Âge")

    class Meta:
        ordering = ("id",)
        verbose_name = "participant"
        verbose_name_plural = "participants"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class EmailLookupAttempt(models.Model):
    """Compteur persistant pour limiter l'énumération des adresses e-mail."""

    ip_hash = models.CharField(max_length=64, unique=True)
    window_started_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = "tentative de recherche"
        verbose_name_plural = "tentatives de recherche"
