from __future__ import annotations

import asyncio
import contextlib
import pathlib
import sys
from types import TracebackType
from typing import Any, Awaitable, ClassVar, Dict, Final, Optional, Tuple, Type, TYPE_CHECKING

from fastai.learner import Learner, load_learner


__all__ = ("LearnerManager",)


class _PosixPathMonkeyPatch(contextlib.AbstractContextManager):

    __slots__ = ("_old_posix_path", "_patched")
    if TYPE_CHECKING:
        _old_posix_path: Type[pathlib.PosixPath]
        _patched: bool

    def __init__(self) -> None:
        self._old_posix_path = pathlib.PosixPath
        self._patched = (sys.platform == "win32")

    def __enter__(self) -> None:
        if self._patched:
            pathlib.PosixPath = pathlib.WindowsPath

    def __exit__(self, exc_type: Optional[Type[BaseException]], exc_value: Optional[BaseException], traceback: Optional[TracebackType]) -> None:
        if self._patched:
            pathlib.PosixPath = self._old_posix_path


class LearnerManager:

    __slots__ = ("__mapping",)
    __instance__: ClassVar[Optional[Learner]] = None
    MODEL_PATH: Final[pathlib.Path] = pathlib.Path("bot/models")
    if TYPE_CHECKING:
        __mapping: Dict[str, Learner]

    def __new__(cls) -> LearnerManager:
        if cls.__instance__ is None:
            self = super().__new__(cls)
            self.__mapping = {}

            cls.__instance__ = self

        return cls.__instance__

    def load_learner(self, name: str, /) -> Awaitable[None]:
        return asyncio.to_thread(self._load_learner, name)

    def _load_learner(self, name: str, /) -> None:
        if name not in self.__mapping:
            with _PosixPathMonkeyPatch():
                self.__mapping[name] = load_learner(self.MODEL_PATH / f"{name}.pkl", cpu=True)

    def predict(self, name: str, *, item: Any, with_input: bool = False) -> Awaitable[Tuple[Any, Any, Any]]:
        learner = self.__mapping[name]
        return asyncio.to_thread(self.silent_predict, learner, item=item, with_input=with_input)

    @staticmethod
    def silent_predict(learner: Learner, *, item: Any, with_input: bool = False) -> Tuple[Any, Any, Any]:
        with learner.no_logging():
            with learner.no_mbar():
                return learner.predict(item, with_input=with_input)

    @classmethod
    async def load_and_predict(cls, name: str, *, item: Any, with_input: bool = False) -> Tuple[Any, Any, Any]:
        self = cls()
        await self.load_learner(name)
        return await self.predict(name, item=item, with_input=with_input)
