from app.modules.settings import CustomBaseSettings


def test_yaml_settings():
    class Conf(CustomBaseSettings):
        a: int
        b: str

    assert Conf("tests/data/config.yml").dict() == {"a": 1, "b": "2"}


def test_env_settings(monkeypatch):
    class Conf(CustomBaseSettings):
        a: int
        b: str

    monkeypatch.setenv("a", "1")
    monkeypatch.setenv("b", "2")
    assert Conf().dict() == {"a": 1, "b": "2"}
