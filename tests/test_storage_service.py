from oae.storage.service import StorageService


def test_storage_service():

    storage = StorageService()

    storage.save("mission", "Mission 061")

    assert storage.exists("mission")
    assert storage.load("mission") == "Mission 061"

    assert storage.delete("mission") is True
    assert storage.exists("mission") is False
