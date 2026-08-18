"""Italian format checks used across the public form."""

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

# Weights of the codice fiscale check character, by position parity. Odd
# positions (counting from one) use their own table; even ones map digits to
# their value and letters to their alphabet index.
_ODD = {
    "0": 1,
    "1": 0,
    "2": 5,
    "3": 7,
    "4": 9,
    "5": 13,
    "6": 15,
    "7": 17,
    "8": 19,
    "9": 21,
    "A": 1,
    "B": 0,
    "C": 5,
    "D": 7,
    "E": 9,
    "F": 13,
    "G": 15,
    "H": 17,
    "I": 19,
    "J": 21,
    "K": 2,
    "L": 4,
    "M": 18,
    "N": 20,
    "O": 11,
    "P": 3,
    "Q": 6,
    "R": 8,
    "S": 12,
    "T": 14,
    "U": 16,
    "V": 10,
    "W": 22,
    "X": 25,
    "Y": 24,
    "Z": 23,
}


def _even(char):
    return int(char) if char.isdigit() else ord(char) - ord("A")


def tax_code_check_character(first_fifteen):
    """The sixteenth character a valid codice fiscale must end with."""
    total = sum(
        _ODD[char] if position % 2 == 0 else _even(char)
        for position, char in enumerate(first_fifteen)
    )
    return chr(ord("A") + total % 26)


def validate_tax_code(value):
    """Refuse a codice fiscale whose check character does not match.

    The checksum catches the transcription slips a length check misses, and it
    accepts omocodia variants, which a positional regex would wrongly reject.
    """
    code = value.upper()
    if len(code) != 16 or not code.isalnum() or not code[:15].isalnum():
        raise ValidationError(_("A tax code is 16 letters and digits."))
    if tax_code_check_character(code[:15]) != code[15]:
        raise ValidationError(_("This tax code is not valid: check for a typo."))


validate_postcode = RegexValidator(
    r"^\d{5}$", _("An Italian postcode is exactly five digits.")
)

validate_phone = RegexValidator(
    r"^\+?[\d\s.\-/]{8,20}$", _("Write the number with digits, spaces or a plus sign.")
)
