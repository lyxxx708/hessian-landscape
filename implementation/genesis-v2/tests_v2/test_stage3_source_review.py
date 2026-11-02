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


def test_data_stays_unapproved_until_review_and_bytes_are_hashed():
    for config in (default_config("full"), load_config(ROOT / "configs" / "study_v2.yaml")):
        source = config["data"]
        assert source["text_expected_sha256"] is None, (
            "No fabricated first-download digest; require SHA256 after actual download, before S1 freeze"
        )
        assert source["text_license_accepted"] is False
        assert source["image_license_accepted"] is False
        assert config["s1_seeds"] == 5
        assert config["s2_seeds"] == 16
