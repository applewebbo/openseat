from django.db.models.utils import get_blank_choice_label
from django.utils import translation


def test_the_blank_choice_label_is_translated_into_italian():
    with translation.override("it"):
        assert str(get_blank_choice_label()) == "Scegli un'opzione"
