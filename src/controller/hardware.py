"""Hardware helpers for controllers."""
import logging

from src.settings import PathBuilder

logger = logging.getLogger(__name__)


def create_printer():
    """Load printer implementation lazily."""
    try:
        from src.hardware import printer

        return printer.EpitPrinter()
    except Exception as e:
        logger.warning("printer is not initialized: %s", e)
        return None


def create_service(view, printer):
    """Instantiate service tool for the given printer."""
    if not printer:
        return None, None

    try:
        from src.hardware import service

        panel = service.ServicePanel(view)
        panel.setModal(True)
        controller = service.ServiceController(panel, service.ServiceModel(printer))
        return panel, controller
    except Exception as e:
        logger.warning("service tool is unavailable: %s", e)
        return None, None


def create_calibration(view, printer):
    """Instantiate calibration tool for the given printer."""
    if not printer:
        return None, None

    try:
        from src.hardware import calibration

        panel = calibration.CalibrationPanel(view)
        panel.setModal(True)
        controller = calibration.CalibrationController(
            panel,
            calibration.CalibrationModel(printer, PathBuilder.calibration_file()),
        )
        return panel, controller
    except Exception as e:
        logger.warning("calibration tool is unavailable: %s", e)
        return None, None
