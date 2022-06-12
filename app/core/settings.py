import warnings
from pathlib import Path
from typing import (
    Any,
    Dict,
    Tuple,
    ClassVar,
    Type,
    Optional,
    AbstractSet,
    List,
    Union,
)
import yaml
from pydantic import BaseSettings, BaseModel, BaseConfig
from pydantic.config import Extra
from pydantic.fields import ModelField
from pydantic.typing import StrPath, display_as_type
from pydantic.env_settings import (
    SettingsSourceCallable,
    InitSettingsSource,
    EnvSettingsSource,
    env_file_sentinel,
)
from pydantic.utils import deep_update, sequence_like


# This class is largely based on the pydantic BaseSettings class
class CustomBaseSettings(BaseModel):
    """
    Base class for settings, allowing values to be overridden by environment variables.
    This is useful in production for secrets you do not wish to save in code, it plays nicely with docker(-compose),
    Heroku and any 12 factor app design.
    """

    def __init__(
        __pydantic_self__,
        _yaml_file: str = None,
        _env_file: Optional[StrPath] = env_file_sentinel,
        _env_file_encoding: Optional[str] = None,
        _env_nested_delimiter: Optional[str] = None,
        _secrets_dir: Optional[StrPath] = None,
        **values: Any,
    ) -> None:
        # Uses something other than `self` the first arg to allow "self" as a settable attribute
        super().__init__(
            **__pydantic_self__._build_values(
                values,
                _yaml_file=_yaml_file,
                _env_file=_env_file,
                _env_file_encoding=_env_file_encoding,
                _env_nested_delimiter=_env_nested_delimiter,
                _secrets_dir=_secrets_dir,
            )
        )

    def _build_values(
        self,
        init_kwargs: Dict[str, Any],
        _yaml_file: Optional[StrPath] = None,
        _env_file: Optional[StrPath] = None,
        _env_file_encoding: Optional[str] = None,
        _env_nested_delimiter: Optional[str] = None,
        _secrets_dir: Optional[StrPath] = None,
    ) -> Dict[str, Any]:
        # Configure built-in sources
        settings = {}
        settings["init_settings"] = InitSettingsSource(init_kwargs=init_kwargs)
        settings["env_settings"] = EnvSettingsSource(
            env_file=(
                _env_file
                if _env_file != env_file_sentinel
                else self.__config__.env_file
            ),
            env_file_encoding=(
                _env_file_encoding
                if _env_file_encoding is not None
                else self.__config__.env_file_encoding
            ),
            env_nested_delimiter=(
                _env_nested_delimiter
                if _env_nested_delimiter is not None
                else self.__config__.env_nested_delimiter
            ),
        )
        if _yaml_file:
            settings["yaml_settings"] = YamlSettingsSource(
                yaml_file=_yaml_file or self.__config__.yaml_file
            )
        # Provide a hook to set built-in sources priority and add / remove sources
        sources = self.__config__.customise_sources(**settings)
        if sources:
            return deep_update(*reversed([source(self) for source in sources]))
        else:
            # no one should mean to do this, but I think returning an empty dict is marginally preferable
            # to an informative error and much better than a confusing error
            return {}

    class Config(BaseConfig):
        yaml_file = None
        env_prefix = ""
        env_file = None
        env_file_encoding = None
        env_nested_delimiter = None
        secrets_dir = None
        validate_all = True
        extra = Extra.forbid
        arbitrary_types_allowed = True
        case_sensitive = False

        @classmethod
        def prepare_field(cls, field: ModelField) -> None:
            env_names: Union[List[str], AbstractSet[str]]
            field_info_from_config = cls.get_field_info(field.name)

            env = field_info_from_config.get("env") or field.field_info.extra.get("env")
            if env is None:
                if field.has_alias:
                    warnings.warn(
                        "aliases are no longer used by BaseSettings to define which environment variables to read. "
                        'Instead use the "env" field setting. '
                        "See https://pydantic-docs.helpmanual.io/usage/settings/#environment-variable-names",
                        FutureWarning,
                    )
                env_names = {cls.env_prefix + field.name}
            elif isinstance(env, str):
                env_names = {env}
            elif isinstance(env, (set, frozenset)):
                env_names = env
            elif sequence_like(env):
                env_names = list(env)
            else:
                raise TypeError(
                    f"invalid field env: {env!r} ({display_as_type(env)}); should be string, list or set"
                )

            if not cls.case_sensitive:
                env_names = env_names.__class__(n.lower() for n in env_names)
            field.field_info.extra["env_names"] = env_names

        @classmethod
        def customise_sources(
            cls,
            init_settings: SettingsSourceCallable = None,
            env_settings: SettingsSourceCallable = None,
            yaml_settings: SettingsSourceCallable = None,
        ) -> Tuple[SettingsSourceCallable, ...]:
            ret_tuple = ()
            if init_settings:
                ret_tuple += (init_settings,)
            if env_settings:
                ret_tuple += (env_settings,)
            if yaml_settings:
                ret_tuple += (yaml_settings,)
            return ret_tuple

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
