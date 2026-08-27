"""The register on the external tracciato the association's other app expects.

Master_Import_Anagrafica.xlsx is that app's own import template: 22 columns, most
of them for entities and details this register never carries (VAT numbers, PEC,
company names — the register is people, never companies). Columns without a home
on Member are always exported blank and ignored on import, so a round trip through
that app never loses data this register does track.
"""

from import_export import fields, resources
from import_export.widgets import CharWidget

from intake.models import Association
from members.models import Member

FIXED_COUNTRY = "IT"


class MemberResource(resources.ModelResource):
    TIPO_ANAGRAFICA = fields.Field(column_name="TIPO_ANAGRAFICA", readonly=True)
    COGNOME = fields.Field(
        attribute="last_name", column_name="COGNOME", widget=CharWidget()
    )
    NOME = fields.Field(attribute="first_name", column_name="NOME", widget=CharWidget())
    SETTORE_ISTITUZIONALE_ENTE = fields.Field(
        column_name="SETTORE_ISTITUZIONALE_ENTE", readonly=True
    )
    DENOMINAZIONE = fields.Field(column_name="DENOMINAZIONE", readonly=True)
    CODICE_FISCALE = fields.Field(
        attribute="tax_code", column_name="CODICE_FISCALE", widget=CharWidget()
    )
    SIGLA_NAZIONE_CODICE_FISCALE = fields.Field(
        column_name="SIGLA_NAZIONE_CODICE_FISCALE", readonly=True
    )
    PARTITA_IVA = fields.Field(column_name="PARTITA_IVA", readonly=True)
    SIGLA_NAZIONE_PARTITA_IVA = fields.Field(
        column_name="SIGLA_NAZIONE_PARTITA_IVA", readonly=True
    )
    INDIRIZZO = fields.Field(
        attribute="street", column_name="INDIRIZZO", widget=CharWidget()
    )
    CIVICO = fields.Field(attribute="number", column_name="CIVICO", widget=CharWidget())
    CAP = fields.Field(attribute="postcode", column_name="CAP", widget=CharWidget())
    COMUNE = fields.Field(attribute="city", column_name="COMUNE", widget=CharWidget())
    SIGLA_PROVINCIA = fields.Field(
        attribute="province", column_name="SIGLA_PROVINCIA", widget=CharWidget()
    )
    SIGLA_NAZIONE = fields.Field(column_name="SIGLA_NAZIONE", readonly=True)
    TELEFONO = fields.Field(column_name="TELEFONO", readonly=True)
    CELLULARE = fields.Field(
        attribute="contact_phone", column_name="CELLULARE", widget=CharWidget()
    )
    EMAIL = fields.Field(attribute="email", column_name="EMAIL", widget=CharWidget())
    PEC = fields.Field(column_name="PEC", readonly=True)
    SITO_WEB = fields.Field(column_name="SITO_WEB", readonly=True)
    NOTE = fields.Field(column_name="NOTE", readonly=True)
    TAG = fields.Field(column_name="TAG", readonly=True)

    class Meta:
        model = Member
        fields = (
            "TIPO_ANAGRAFICA",
            "COGNOME",
            "NOME",
            "SETTORE_ISTITUZIONALE_ENTE",
            "DENOMINAZIONE",
            "CODICE_FISCALE",
            "SIGLA_NAZIONE_CODICE_FISCALE",
            "PARTITA_IVA",
            "SIGLA_NAZIONE_PARTITA_IVA",
            "INDIRIZZO",
            "CIVICO",
            "CAP",
            "COMUNE",
            "SIGLA_PROVINCIA",
            "SIGLA_NAZIONE",
            "TELEFONO",
            "CELLULARE",
            "EMAIL",
            "PEC",
            "SITO_WEB",
            "NOTE",
            "TAG",
        )

    def __init__(self, mode="overwrite", **kwargs):
        super().__init__(**kwargs)
        self.mode = mode
        self.association = Association.current()

    def dehydrate_SIGLA_NAZIONE_CODICE_FISCALE(self, member):
        return FIXED_COUNTRY

    def dehydrate_SIGLA_NAZIONE(self, member):
        return FIXED_COUNTRY

    def dehydrate_EMAIL(self, member):
        """A minor carries no email of their own — only the signing contact's.

        Falls back to contact_email on export so the tracciato never shows a
        blank cell for someone the register does have an address for.
        """
        return member.email or member.contact_email

    def dehydrate_NOTE(self, member):
        """The event the member joined through, blank for a hand-entered row."""
        submission = member.submission
        if submission is None or not hasattr(submission, "booking"):
            return ""
        event = submission.booking.event
        return f"{event.title} - {event.starts_at.strftime('%d/%m/%Y')}"

    def get_queryset(self):
        return Member.objects.filter(association=self.association)

    def get_instance(self, instance_loader, row):
        """Match on tax code within the association — never in append mode.

        A blank tax code in the source row is always treated as a new row: there
        is nothing to match on, and matching on an empty string would collapse
        every member without one onto a single row.
        """
        if self.mode == "append":
            return None
        tax_code = (row.get("CODICE_FISCALE") or "").strip()
        if not tax_code:
            return None
        return Member.objects.filter(
            association=self.association, tax_code__iexact=tax_code
        ).first()

    def before_save_instance(self, instance, row, **kwargs):
        instance.association = self.association
        if not instance.contact_email:
            instance.contact_email = instance.email
        if not instance.contact_name:
            instance.contact_name = (
                f"{instance.first_name} {instance.last_name}".strip()
            )
