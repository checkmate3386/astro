from django import forms


MAX_PARTICIPANTS = 6
AGE_CHOICES = [("", "—")] + [(str(age), str(age)) for age in range(1, 19)]


class RegistrationForm(forms.Form):
    email = forms.EmailField(label="Adresse e-mail", max_length=254)
    email_confirm = forms.EmailField(
        label="Confirmer l’adresse e-mail",
        max_length=254,
    )
    people_count = forms.ChoiceField(
        label="Nombre de personnes",
        choices=[(str(count), str(count)) for count in range(1, MAX_PARTICIPANTS + 1)],
    )
    brings_equipment = forms.BooleanField(
        label="J’amène du matériel astro",
        required=False,
    )
    equipment_description = forms.CharField(
        label="Qu’est-ce que j’amène ?",
        required=False,
        max_length=2000,
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    def __init__(self, *args, **kwargs):
        self.initial_participants = kwargs.pop("participants", [])
        if "initial" not in kwargs:
            kwargs["initial"] = {}
        kwargs["initial"].setdefault(
            "people_count",
            str(max(1, len(self.initial_participants))),
        )
        super().__init__(*args, **kwargs)

        for index in range(MAX_PARTICIPANTS):
            participant = (
                self.initial_participants[index]
                if index < len(self.initial_participants)
                else {}
            )
            self.fields[f"first_name_{index}"] = forms.CharField(
                label="Prénom",
                required=False,
                max_length=100,
                initial=participant.get("first_name", ""),
            )
            self.fields[f"last_name_{index}"] = forms.CharField(
                label="Nom",
                required=False,
                max_length=100,
                initial=participant.get("last_name", ""),
            )
            self.fields[f"is_minor_{index}"] = forms.BooleanField(
                label="Le participant est mineur",
                required=False,
                initial=participant.get("is_minor", False),
            )
            self.fields[f"age_{index}"] = forms.ChoiceField(
                label="Âge",
                choices=AGE_CHOICES,
                required=False,
                initial=(
                    str(participant["age"])
                    if participant.get("age") is not None
                    else ""
                ),
            )

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean_email_confirm(self):
        return self.cleaned_data["email_confirm"].strip().lower()

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        email_confirm = cleaned_data.get("email_confirm")
        if email and email_confirm and email != email_confirm:
            self.add_error("email_confirm", "Les deux adresses e-mail doivent être identiques.")

        try:
            count = int(cleaned_data.get("people_count", "0"))
        except (TypeError, ValueError):
            count = 0

        participants = []
        for index in range(count):
            first_name = cleaned_data.get(f"first_name_{index}", "").strip()
            last_name = cleaned_data.get(f"last_name_{index}", "").strip()
            is_minor = cleaned_data.get(f"is_minor_{index}", False)
            age_value = cleaned_data.get(f"age_{index}", "")

            if not first_name:
                self.add_error(f"first_name_{index}", "Le prénom est obligatoire.")
            if not last_name:
                self.add_error(f"last_name_{index}", "Le nom est obligatoire.")

            age = None
            if is_minor:
                if not age_value:
                    self.add_error(f"age_{index}", "L’âge est obligatoire pour un mineur.")
                else:
                    age = int(age_value)
            participants.append(
                {
                    "first_name": first_name,
                    "last_name": last_name,
                    "is_minor": is_minor,
                    "age": age,
                }
            )

        cleaned_data["participants"] = participants
        if (
            not cleaned_data.get("brings_equipment")
            and cleaned_data.get("equipment_description")
        ):
            cleaned_data["equipment_description"] = ""
        if cleaned_data.get("brings_equipment") and not cleaned_data.get(
            "equipment_description", ""
        ).strip():
            self.add_error(
                "equipment_description",
                "Précisez le matériel que vous apportez.",
            )
        return cleaned_data
