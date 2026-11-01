import pytest

from geo_check.analysis import competitor_candidates, count_mentions, domain_of, rank_domains
from geo_check.questions import generate_questions


def test_questions_pt_and_en():
    pt = generate_questions("dentista", "Campinas", "pt")
    en = generate_questions("dentist", "Campinas", "en")
    assert len(pt) == 5 and len(en) == 5
    assert all("dentista" in q and "Campinas" in q for q in pt)
    assert pt[0].startswith("Qual")
    assert en[0].startswith("What")


def test_questions_bad_lang():
    with pytest.raises(ValueError):
        generate_questions("a", "b", "fr")


def test_mentions_case_and_accent_insensitive():
    text = "A CLÍNICA exemplo é boa. Clinica Exemplo atende bem. clínica   exemplo!"
    assert count_mentions(text, "Clinica Exemplo") == 3


def test_mentions_whole_word_only():
    assert count_mentions("Acme Corporation and Acmeville", "Acme") == 1
    assert count_mentions("nothing here", "Acme") == 0
    assert count_mentions("anything", "") == 0


def test_domains_ranked():
    urls = [
        "https://www.a.com/x",
        "https://a.com/y",
        "http://b.org/z",
        "https://www.a.com:443/q",
    ]
    assert domain_of("https://www.a.com/x") == "a.com"
    assert rank_domains(urls) == [("a.com", 3), ("b.org", 1)]


def test_competitor_candidates_exclude_brand():
    texts = ["1. **Clínica Alfa** is great. Also Beta Dental. **Clinica Exemplo** too."]
    names = [n for n, _ in competitor_candidates(texts, "Clinica Exemplo")]
    assert "Clínica Alfa" in names
    assert not any("Exemplo" in n for n in names)
