from oae.core.patch_generator import PatchGenerator


def test_generate_empty_plan():
    generator = PatchGenerator()

    plan = {
        "mission": {},
        "steps": [],
    }

    result = generator.generate(plan)

    assert result["status"] == "generated"
    assert result["plan"] == plan
    assert result["patches"] == []


def test_generate_single_patch():
    generator = PatchGenerator()

    plan = {
        "mission": {
            "type": "remove_dead_code",
        },
        "steps": [
            "analyze",
            "generate_patch",
            "verify",
            "execute",
        ],
    }

    result = generator.generate(plan)

    assert result["status"] == "generated"
    assert result["plan"]["mission"]["type"] == "remove_dead_code"


def test_patch_structure():
    generator = PatchGenerator()

    result = generator.generate(
        {
            "mission": {},
            "steps": [],
        }
    )

    assert "status" in result
    assert "plan" in result
    assert "patches" in result
