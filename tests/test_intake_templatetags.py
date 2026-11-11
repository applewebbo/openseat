import pytest

from intake.templatetags.intake_extras import render_custom_body

pytestmark = pytest.mark.django_db


def test_a_known_placeholder_is_substituted(association):
    association.name = "Circolo Vela Novara"

    result = render_custom_body("<p>Benvenuto in {association_name}</p>", association)

    assert result == "<p>Benvenuto in Circolo Vela Novara</p>"


def test_the_membership_fee_placeholder_is_substituted(association):
    association.membership_fee = "25.00"

    result = render_custom_body("Quota: € {membership_fee}", association)

    assert result == "Quota: € 25.00"


def test_an_unknown_placeholder_is_left_untouched(association):
    result = render_custom_body("Ciao {nome_socio}", association)

    assert result == "Ciao {nome_socio}"


def test_a_malformed_brace_never_raises(association):
    result = render_custom_body("Orario: 9} - 18", association)

    assert result == "Orario: 9} - 18"


def test_an_empty_value_is_returned_as_is(association):
    assert render_custom_body("", association) == ""
