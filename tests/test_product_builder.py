from oae.core.product_builder import build_product_brief


def test_product_builder_fallback_understands_school_product():
    brief = build_product_brief(
        "Build a school management app where admins register students, teachers take attendance, parents see results, and the school collects fees."
    )
    assert "School administrators" in brief["users"]
    assert "Student" in brief["entities"]
    assert brief["payments"] is True
    assert brief["build_ready"] is False
    assert brief["missing"]

def test_product_builder_fallback_never_claims_delivery():
    brief = build_product_brief("Build a simple inventory app for my shop.")
    assert "deployment" in brief
    assert "tested" not in str(brief).lower()
    assert "deployed" not in str(brief).lower()


def test_product_builder_fallback_localizes_supported_languages():
    expected = {
        "it": "Nuovo prodotto",
        "de": "Neues Produkt",
        "fr": "Nouveau produit",
        "es": "Producto nuevo",
        "pt": "Novo produto",
        "ar": "منتج جديد",
        "yo": "Ọjà tuntun",
        "ha": "Sabon samfuri",
        "ig": "Ngwaahịa ọhụrụ",
    }
    for language, product_name in expected.items():
        brief = build_product_brief("Build an app for my business.", language=language)
        assert brief["product_name"] == product_name
        assert brief["auth"] != ""
        assert brief["deployment"] != ""
