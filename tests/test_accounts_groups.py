import pytest
from django.contrib.auth.models import Group, Permission
from django.core.management import call_command
from django.urls import reverse

from accounts.groups import EDITORS, ensure_editor_group

pytestmark = pytest.mark.django_db


@pytest.fixture
def editor(user):
    """A volunteer who may publish events and nothing else."""
    user.is_staff = True
    user.save()
    user.groups.add(ensure_editor_group())
    return user


@pytest.fixture
def editor_client(client, editor):
    client.force_login(editor)
    return client


def codenames(group):
    return set(group.permissions.values_list("codename", flat=True))


class TestTheGroup:
    def test_it_grants_events_and_nothing_else(self):
        group = ensure_editor_group()

        apps = set(group.permissions.values_list("content_type__app_label", flat=True))
        assert apps == {"events"}

    def test_a_booking_can_be_corrected_but_not_deleted(self):
        """Withdrawing a place is cancel(), which leaves a trace; deleting the
        row loses who booked and when."""
        group = ensure_editor_group()

        assert "delete_booking" not in codenames(group)
        assert {"add_booking", "change_booking", "view_booking"} <= codenames(group)

    def test_an_event_can_be_deleted(self):
        assert "delete_event" in codenames(ensure_editor_group())

    def test_running_it_again_leaves_one_group(self):
        ensure_editor_group()
        ensure_editor_group()

        assert Group.objects.filter(name=EDITORS).count() == 1

    def test_a_permission_added_by_hand_is_taken_back(self):
        """The group is a definition, not a starting point: it is reset to it."""
        group = ensure_editor_group()
        group.permissions.add(Permission.objects.get(codename="delete_booking"))

        ensure_editor_group()

        assert "delete_booking" not in codenames(group)

    def test_the_command_creates_it(self, capsys):
        call_command("accounts_groups")

        assert Group.objects.filter(name=EDITORS).exists()
        assert EDITORS in capsys.readouterr().out


class TestWhatAnEditorSees:
    def test_the_events_changelist_is_open(self, editor_client, event):
        response = editor_client.get(reverse("admin:events_event_changelist"))

        assert response.status_code == 200

    def test_the_register_is_closed(self, editor_client, member):
        response = editor_client.get(reverse("admin:members_member_changelist"))

        assert response.status_code == 403

    def test_the_applications_are_closed(self, editor_client, minor_submission):
        response = editor_client.get(reverse("admin:intake_submission_changelist"))

        assert response.status_code == 403

    def test_the_association_is_closed(self, editor_client, association):
        response = editor_client.get(reverse("admin:intake_association_changelist"))

        assert response.status_code == 403

    def test_the_admin_index_offers_only_events(self, editor_client, event):
        content = editor_client.get(reverse("admin:index")).content.decode()

        assert reverse("admin:events_event_changelist") in content
        assert reverse("admin:members_member_changelist") not in content

    def test_deleting_a_booking_is_refused(self, editor_client, booking):
        response = editor_client.get(
            reverse("admin:events_booking_delete", args=[booking.pk])
        )

        assert response.status_code == 403

    def test_someone_without_the_group_sees_no_events(self, client, user):
        user.is_staff = True
        user.save()
        client.force_login(user)

        response = client.get(reverse("admin:events_event_changelist"))

        assert response.status_code == 403
