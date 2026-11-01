from pathlib import Path

from geo_check.analysis import competitor_candidates

FIX = Path(__file__).parent / "fixtures"


def _read(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8")


def _names(texts, brand, **kw):
    return [n for n, _ in competitor_candidates(texts, brand, **kw)]


JUNK = ["Antes", "Não", "Clínica", "CRO-SP", "Doctoralia", "Campinas", "Registro"]


def test_real_perplexity_junk_fixture_pt():
    names = _names(
        [_read("junk_fixture_pt.md")], "OdontoCompany",
        category="dentista", city="Campinas", platforms=["doctoralia.com.br"],
    )
    assert sorted(names) == sorted(
        ["Dra. Júlia Jacob", "Dr. Sérgio Moura Guimarães", "Clínica Sorriso Campinas"]
    )
    for junk in JUNK + ["CRO-SP. Clínica", "OdontoCompany"]:
        assert junk not in names


def test_junk_dropped_even_without_platform_param_and_args():
    # Doctoralia is a well-known platform; CRO-SP a registry; sentence-start words dropped.
    names = _names([_read("junk_fixture_pt.md")], "OdontoCompany")
    for junk in ["Antes", "Não", "Clínica", "CRO-SP", "Doctoralia", "Registro", "CRO-SP. Clínica"]:
        assert junk not in names
    assert "Dra. Júlia Jacob" in names


def test_platform_param_excludes_custom_domain():
    text = "Veja o ranking no Zetaguide. **Clínica Sorriso Campinas** é citada."
    without = _names([text], "X", category="dentista", city="Campinas")
    with_p = _names([text], "X", category="dentista", city="Campinas", platforms=["www.zetaguide.com.br"])
    assert "Zetaguide" in without
    assert "Zetaguide" not in with_p
    assert "Clínica Sorriso Campinas" in with_p


def test_english_answer_fixture():
    names = _names(
        [_read("answer_en.md")], "Acme Dental",
        category="dentist", city="Boston", platforms=["healthgrades.com", "yelp.com"],
    )
    for good in ["Dr. Emily Carter", "Smile Dental Group", "Bright Smiles Dentistry", "Prof. Daniel Reyes"]:
        assert good in names
    for junk in ["Before", "Not", "Check", "Top Picks", "Boston", "ADA", "BBB", "Yelp",
                 "Healthgrades", "Better Business Bureau", "Reviews", "Also", "Always", "Dentist"]:
        assert junk not in names


def test_portuguese_structure_fixture():
    names = _names(
        [_read("answer_pt_2.md")], "OdontoCompany",
        category="dentista", city="Campinas", platforms=["doctoralia.com.br", "reclameaqui.com.br"],
    )
    for good in ["Odonto Vida", "Instituto Bem Estar", "Clínica Sorriso Campinas"]:
        assert good in names
    assert any("Sérgio" in n or "Sergio" in n for n in names)
    for junk in ["Dicas Finais", "Preço", "Consulte", "Procon", "Reclame Aqui", "Doctoralia",
                 "CRO-SP", "Atenção", "Segundo", "Pesquise", "Conselho Regional de Odontologia",
                 "Veja", "Campinas"]:
        assert junk not in names


def test_never_crosses_sentence_punctuation():
    names = _names(["Registro no CRO-SP. Clínica Sorriso atende. Beta Gama, Delta Épsilon."], "X")
    assert "CRO-SP. Clínica" not in names
    assert not any("." in n.replace("Dr.", "").replace("Dra.", "") for n in names)
    assert "Beta Gama" in names and "Delta Épsilon" in names
    assert not any("Gama Delta" in n for n in names)


def test_sentence_start_single_word_needs_midsentence_evidence():
    # "Sorriso" opens a sentence in one answer but appears mid-sentence elsewhere -> kept.
    texts = ["Sorriso atende bem.", "A equipe do Sorriso é ótima."]
    assert "Sorriso" in _names(texts, "X")
    # "Porém" only ever opens sentences -> dropped; "Lumina" never mid-sentence -> dropped.
    assert _names(["Lumina atende bem. Porém cobra caro."], "X") == []


def test_merge_dedup_accent_case_and_title():
    texts = [
        "**Dra. Júlia Jacob** é ótima.",
        "Recomendo a doutora Julia Jacob.",
        "Também **JULIA JACOB** atende.",
        "Marque com Júlia Jacob hoje.",
    ]
    out = competitor_candidates(texts, "X")
    names = [n for n, _ in out]
    assert names.count("Dra. Júlia Jacob") == 1
    assert len([n for n in names if "ulia" in n.lower() or "úlia" in n.lower()]) == 1
    assert dict(out)["Dra. Júlia Jacob"] == 4  # one answer each, all four merged


def test_generic_category_and_city_excluded():
    texts = ["- **Dentistas** são ótimos.\n- **Campinas**: cidade.\n- **Clínica Odontológica**: genérico."]
    assert _names(texts, "X", category="dentista", city="Campinas") == []


def test_brand_excluded_with_accents():
    assert "Clínica Exemplo" not in _names(["**Clinica Exemplo** é boa."], "Clínica Exemplo")
