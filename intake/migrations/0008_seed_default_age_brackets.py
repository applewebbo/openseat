from django.db import migrations

DEFAULT_BRACKETS = [
    ("0-12", 0, 12, 0),
    ("13-17", 13, 17, 1),
    ("18-64", 18, 64, 2),
    ("65+", 65, None, 3),
]


def seed_default_brackets(apps, schema_editor):
    Association = apps.get_model("intake", "Association")
    AgeBracket = apps.get_model("intake", "AgeBracket")
    for association in Association.objects.all():
        if association.age_brackets.exists():
            continue
        AgeBracket.objects.bulk_create(
            [
                AgeBracket(
                    association=association,
                    label=label,
                    min_age=min_age,
                    max_age=max_age,
                    order=order,
                )
                for label, min_age, max_age, order in DEFAULT_BRACKETS
            ]
        )


class Migration(migrations.Migration):
    dependencies = [
        ("intake", "0007_agebracket"),
    ]

    operations = [
        migrations.RunPython(seed_default_brackets, migrations.RunPython.noop),
    ]
