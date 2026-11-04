"""Pre-freeze source review: no old PG #100 source, no invented upfront digest.

This test verifies configuration consistency only. It is NOT a copyright opinion,
download receipt or a pass for a source whose rights remain undecided.
"""
from pathlib import Path
from genesis_gpu.study.design import default_config, load_config


ROOT = Path(__file__).resolve().parents[1]


def test_full_text_source_matches_prospective_edition():
    expected = default_config("full")["data"]
    actual = load_config(ROOT / "configs" / "study_v2.yaml")["data"]
    assert actual["text_url"] == expected["text_url"]
    assert actual["text_url"] == (
        "https://www.gutenberg.org/cache/epub/2270/pg2270.txt"
    )
    assert "100/pg100" not in actual["text_url"]
    assert "First Folio" in actual["text_license"]
    assert "local" in actual["text_license"].lower()


def test_full_data_sources_are_owner_authorized_and_bytes_are_pinned():
    default = default_config("full")
    actual = load_config(ROOT / "configs" / "study_v2.yaml")
    # Generic defaults stay unapproved; this study config records its actual owner decisions.
    assert default["data"]["text_expected_sha256"] is None
    assert default["data"]["text_license_accepted"] is False
    source = actual["data"]
    assert source["text_expected_sha256"] == "f7903c30b83ccaaef85f024746c693a6f7f63c1c926075c998ea67c4732680a4"
    assert source["text_license_accepted"] is True
    assert source["image_license_accepted"] is True
    assert "owner authorized local research" in source["text_license"]
    assert "no redistribution" in source["text_license"]
    assert actual["s1_seeds"] == 5
    assert actual["s2_seeds"] == 16
