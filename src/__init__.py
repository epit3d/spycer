"""Core package exposing primary interfaces for Spycer."""

try:  # pragma: no cover - optional Qt dependencies
    from .window import MainWindow
    from .controller import MainController
except Exception:  # when Qt is missing during lightweight imports
    MainWindow = None  # type: ignore
    MainController = None  # type: ignore

__all__ = ["MainWindow", "MainController"]
