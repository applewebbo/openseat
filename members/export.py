"""The register as a file the treasurer can open."""

import csv

COLUMNS = [
    "Cognome",
    "Nome",
    "Data di nascita",
    "Luogo di nascita",
    "Codice fiscale",
    "Residenza",
    "Contatto",
    "Email contatto",
    "Telefono contatto",
    "Data iscrizione",
    "Ratifica",
]


def member_rows(members):
    """Header first, then one row per member. Italian headings: this is a file
    that leaves the app for an accountant or an annual filing."""
    yield COLUMNS
    for member in members:
        residence = " ".join(
            part for part in (member.street, member.number) if part
        )
        if member.city:
            residence = f"{residence}, {member.postcode} {member.city}".strip()
        yield [
            member.last_name,
            member.first_name,
            member.birth_date.strftime("%d/%m/%Y") if member.birth_date else "",
            member.birth_place,
            member.tax_code,
            residence.strip(", "),
            member.contact_name,
            member.contact_email,
            member.contact_phone,
            member.joined_on.strftime("%d/%m/%Y"),
            # An empty cell reads as an oversight; the register should say which
            # admissions the board has still to minute.
            member.ratified_on.strftime("%d/%m/%Y")
            if member.ratified_on
            else "Da ratificare",
        ]


def write_csv(destination, members):
    writer = csv.writer(destination)
    writer.writerows(member_rows(members))
    return members.count()
