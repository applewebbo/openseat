from intake.geo import comune_choices, province_choices


def test_province_are_sorted_alphabetically_by_name():
    nomi = [nome for _sigla, nome in province_choices()]

    assert nomi == sorted(nomi)


def test_the_label_is_the_name_but_the_stored_value_is_the_sigla():
    choices = dict(province_choices())

    assert choices["NO"] == "Novara"


def test_comuni_are_scoped_to_their_own_province():
    novara_comuni = dict(comune_choices("NO"))

    assert "Novara" in novara_comuni
    assert "Milano" not in novara_comuni


def test_an_unknown_province_has_no_comuni():
    assert comune_choices("ZZ") == []
