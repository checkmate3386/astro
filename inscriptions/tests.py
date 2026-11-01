import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Participant, Registration


class EventRegistrationTests(TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.events_path = Path(self.temporary_directory.name) / "events.json"
        self.events_path.write_text(
            json.dumps(
                [
                    {
                        "id": "test-key-not-a-url",
                        "titre": "Soirée test",
                        "description": "Description de test",
                        "details": ["Détail"],
                        "limite": 2,
                    }
                ],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        self.events_patcher = patch("inscriptions.events.EVENTS_FILE", self.events_path)
        self.events_patcher.start()
        self.event_url = reverse("event-detail", kwargs={"slug": "soiree-test"})

    def tearDown(self):
        self.events_patcher.stop()
        self.temporary_directory.cleanup()

    def registration_data(self, email, count, names):
        data = {
            "action": "signup",
            "email": email,
            "email_confirm": email,
            "people_count": str(count),
            "brings_equipment": "",
            "equipment_description": "",
        }
        for index, (first_name, last_name) in enumerate(names):
            data[f"first_name_{index}"] = first_name
            data[f"last_name_{index}"] = last_name
            data[f"is_minor_{index}"] = ""
            data[f"age_{index}"] = ""
        return data

    def test_registration_cannot_exceed_event_capacity(self):
        self.client.post(
            self.event_url,
            self.registration_data("first@example.org", 2, [("Ada", "Lovelace"), ("Alan", "Turing")]),
        )
        response = self.client.post(
            self.event_url,
            self.registration_data("second@example.org", 1, [("Grace", "Hopper")]),
        )

        self.assertContains(response, "Il n’y a plus de place disponible.")
        self.assertEqual(Participant.objects.count(), 2)
        self.assertEqual(Registration.objects.count(), 1)

    def test_email_confirmation_is_validated_on_server(self):
        response = self.client.post(
            self.event_url,
            self.registration_data("club@example.org", 1, [("Ada", "Lovelace")])
            | {"email_confirm": "different@example.org"},
        )

        self.assertContains(response, "Les deux adresses e-mail doivent être identiques.")
        self.assertEqual(Registration.objects.count(), 0)

    def test_registration_can_be_modified_and_participant_count_reduced(self):
        self.client.post(
            self.event_url,
            self.registration_data("club@example.org", 2, [("Ada", "Lovelace"), ("Alan", "Turing")]),
        )
        response = self.client.post(
            self.event_url,
            {"action": "lookup", "email": "club@example.org"},
        )

        self.assertContains(response, "Ada")
        self.assertContains(response, 'data-index="1">')
        self.assertContains(response, 'data-index="2" hidden>')
        self.assertEqual(response.context["active_tab"], "modify")
        update_data = {
            "action": "update",
            "original_email": "club@example.org",
            "email": "club@example.org",
            "email_confirm": "club@example.org",
            "people_count": "1",
            "brings_equipment": "",
            "equipment_description": "",
            "first_name_0": "Ada",
            "last_name_0": "Lovelace-Byron",
            "is_minor_0": "",
            "age_0": "",
        }
        response = self.client.post(self.event_url, update_data)

        self.assertRedirects(response, self.event_url)
        self.assertEqual(Participant.objects.count(), 1)
        self.assertEqual(Participant.objects.get().last_name, "Lovelace-Byron")

    def test_participant_form_shows_only_selected_count(self):
        response = self.client.get(self.event_url)

        self.assertEqual(response.context["visible_participant_count"], 1)
        self.assertContains(response, 'data-index="0">')
        self.assertContains(response, 'data-index="1" hidden>')

    def test_full_event_allows_edit_without_increasing_participants(self):
        self.client.post(
            self.event_url,
            self.registration_data("club@example.org", 2, [("Ada", "Lovelace"), ("Alan", "Turing")]),
        )
        update_data = {
            "action": "update",
            "original_email": "club@example.org",
            "email": "club@example.org",
            "email_confirm": "club@example.org",
            "people_count": "2",
            "brings_equipment": "",
            "equipment_description": "",
            "first_name_0": "Ada",
            "last_name_0": "Lovelace",
            "is_minor_0": "",
            "age_0": "",
            "first_name_1": "Alan",
            "last_name_1": "Changed",
            "is_minor_1": "",
            "age_1": "",
        }

        response = self.client.post(self.event_url, update_data)

        self.assertRedirects(response, self.event_url)
        self.assertEqual(Participant.objects.count(), 2)
        self.assertTrue(Participant.objects.filter(last_name="Changed").exists())

    def test_over_capacity_request_reports_remaining_places(self):
        self.client.post(
            self.event_url,
            self.registration_data("first@example.org", 1, [("Ada", "Lovelace")]),
        )
        response = self.client.post(
            self.event_url,
            self.registration_data(
                "second@example.org",
                2,
                [("Grace", "Hopper"), ("Katherine", "Johnson")],
            ),
        )

        self.assertContains(response, "Il ne reste que 1 place(s)")
        self.assertEqual(Participant.objects.count(), 1)

    def test_event_id_is_not_in_url_and_robots_header_is_present(self):
        response = self.client.get(self.event_url)
        robots = self.client.get("/robots.txt")

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "test-key-not-a-url")
        self.assertIn("X-Robots-Tag", response)
        self.assertEqual(robots.content.decode(), "User-agent: *\nDisallow: /\n")

    def test_home_carousel_handles_zero_and_one_event(self):
        self.events_path.write_text("[]", encoding="utf-8")
        empty_response = self.client.get("/")
        self.assertContains(empty_response, "Aucune soirée programmée")
        self.assertNotContains(empty_response, "carousel-dots")

        self.events_path.write_text(
            json.dumps(
                [
                    {
                        "id": "test-key-not-a-url",
                        "titre": "Soirée test",
                        "description": "Description de test",
                        "details": ["Détail"],
                        "limite": 2,
                    }
                ],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        single_response = self.client.get("/")
        self.assertContains(single_response, "Soirée test")
        self.assertContains(single_response, 'data-slide-index="0"')
        self.assertNotContains(single_response, "test-key-not-a-url")

    def test_home_carousel_hides_inactive_events(self):
        events = [
            {
                "id": "first",
                "titre": "Première soirée",
                "description": "Première description",
                "details": [],
                "limite": 2,
            },
            {
                "id": "second",
                "titre": "Deuxième soirée",
                "description": "Deuxième description",
                "details": [],
                "limite": 2,
            },
        ]
        self.events_path.write_text(
            json.dumps(events, ensure_ascii=False),
            encoding="utf-8",
        )

        response = self.client.get("/")
        html = response.content.decode()

        self.assertRegex(html, r'<a class="slide is-active"\s+href="/soirees/premiere-soiree/"')
        self.assertRegex(
            html,
            r'<a class="slide"\s+href="/soirees/deuxieme-soiree/"\s+hidden\b',
        )
        self.assertContains(response, 'data-slide-index="1"')

    def test_removed_event_page_disappears_but_registration_is_retained(self):
        self.client.post(
            self.event_url,
            self.registration_data("club@example.org", 1, [("Ada", "Lovelace")]),
        )
        self.events_path.write_text("[]", encoding="utf-8")

        response = self.client.get(self.event_url)

        self.assertEqual(response.status_code, 404)
        self.assertIn("X-Robots-Tag", response)
        self.assertEqual(Registration.objects.count(), 1)

    def test_collected_static_file_is_served_with_robots_header(self):
        static_root = Path(self.temporary_directory.name) / "staticfiles"
        css_directory = static_root / "css"
        css_directory.mkdir(parents=True)
        (css_directory / "site.css").write_text("body { color: white; }", encoding="utf-8")
        with override_settings(
            STATIC_ROOT=static_root,
            DEBUG=False,
            ALLOWED_HOSTS=["testserver"],
        ):
            response = self.client.get("/static/css/site.css")

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/css", response["Content-Type"])
        self.assertIn("X-Robots-Tag", response)

    @override_settings(EMAIL_LOOKUP_LIMIT=2)
    def test_email_lookup_attempts_are_limited_by_ip(self):
        first = self.client.post(
            self.event_url,
            {"action": "lookup", "email": "unknown@example.org"},
        )
        second = self.client.post(
            self.event_url,
            {"action": "lookup", "email": "unknown@example.org"},
        )
        blocked = self.client.post(
            self.event_url,
            {"action": "lookup", "email": "unknown@example.org"},
        )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertRedirects(blocked, self.event_url)
