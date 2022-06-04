from pathlib import Path
from typing import (
    Any,
    Dict,
    Tuple,
    ClassVar,
    Type,
)
import yaml
from pydantic import BaseSettings, BaseModel, BaseConfig
from pydantic.typing import StrPath
from pydantic.env_settings import SettingsSourceCallable, InitSettingsSource
from pydantic.utils import deep_update


# This class is largely based on the pydantic BaseSettings class
class CustomBaseSettings(BaseModel):
    """
    Base class for settings, allowing values to be overridden by environment variables.
    This is useful in production for secrets you do not wish to save in code, it plays nicely with docker(-compose),
    Heroku and any 12 factor app design.
    """

    def __init__(
        __pydantic_self__,
        _yaml_file: str,
        **values: Any,
    ) -> None:
        # Uses something other than `self` the first arg to allow "self" as a settable attribute
        super().__init__(
            **__pydantic_self__._build_values(values, _yaml_file=_yaml_file)
        )

    def _build_values(
        self,
        init_kwargs: Dict[str, Any],
        _yaml_file: StrPath,
    ) -> Dict[str, Any]:
        # Configure built-in sources
        init_settings = InitSettingsSource(init_kwargs=init_kwargs)
        yaml_settings = YamlSettingsSource(
            yaml_file=_yaml_file or self.__config__.yaml_file
        )
        # Provide a hook to set built-in sources priority and add / remove sources
        sources = self.__config__.customise_sources(
            init_settings=init_settings,
            yaml_settings=yaml_settings,
        )
        if sources:
            return deep_update(*reversed([source(self) for source in sources]))
        else:
            # no one should mean to do this, but I think returning an empty dict is marginally preferable
            # to an informative error and much better than a confusing error
            return {}

    class Config(BaseConfig):
        yaml_file = None

        @classmethod
        def customise_sources(
            cls,
            init_settings: SettingsSourceCallable,
            yaml_settings: SettingsSourceCallable,
        ) -> Tuple[SettingsSourceCallable, ...]:
            return init_settings, yaml_settings

    # populated by the metaclass using the Config class defined above, annotated here to help IDEs only
    __config__: ClassVar[Type[Config]]


class YamlSettingsSource:
    __slots__ = ("yaml_file",)

    def __init__(self, yaml_file: StrPath):
        self.yaml_file: StrPath = yaml_file

    def __call__(self, settings: BaseSettings) -> Dict[str, Any]:
        path = Path(self.yaml_file)
        content = {}
        if path.exists():
            with open(path, "r", encoding=None) as f:
                content = yaml.safe_load(f)
        return content

    def __repr__(self) -> str:
        return f"YamlSettingsSource(yaml_file={self.yaml_file!r})"
