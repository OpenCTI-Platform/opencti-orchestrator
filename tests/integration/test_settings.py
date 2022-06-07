from app.modules.settings import CustomBaseSettings


def test_yaml_settings():
    class Conf(CustomBaseSettings):
        a: int
        b: str

    assert Conf("tests/data/config.yml").dict() == {'a': 1, 'b': '2'}