from loguru import logger
from sys import stdout, stderr

_event_format = "{time:DD/MM/YYYY HH:mm:ss:SS} | <lvl>{level}</> | <lvl>{message}</>"
_issue_format = "{time:DD/MM/YYYY HH:mm:ss:SS} | <lvl>{level}</> | <lvl>{message}</> | {file}:{line} {exception}"
_rotation_duration = "1 week"
_retention_duration = "1 month"
_compression_type = "gz"
_default_event_level = "TRACE"
_default_issue_level = "WARNING"


def setup_logger(log_folder_path: str,level: str) -> None:
    logger.remove()
    add_event_console(_default_event_level)
    add_issue_console(_default_issue_level)
    add_event_log_file(_default_event_level, log_folder_path)
    add_issue_log_file(_default_issue_level, log_folder_path)
    set_colors()


def add_event_console(log_level: str) -> None:
    logger.add(
        stdout,
        format=_event_format,
        level=log_level,
        colorize=True,
        filter=lambda record: record["level"].no < logger.level(_default_issue_level).no
    )


def add_issue_console(log_level: str) -> None:
    logger.add(
        stderr,
        format=_issue_format,
        level=log_level,
        colorize=True
    )


def add_event_log_file(log_level: str,log_folder_path: str) -> None:
    logger.add(
        log_folder_path + "/events/events.log",
        format=_event_format,
        rotation=_rotation_duration,
        retention=_retention_duration,
        level=log_level,
        filter=lambda record: record["level"].no < logger.level(_default_issue_level).no,
        compression=_compression_type
    )


def add_issue_log_file(log_level: str,log_folder_path: str) -> None:
    logger.add(
        log_folder_path + "/issues/issues.log",
        format=_issue_format,
        rotation=_rotation_duration,
        retention=_retention_duration,
        level=log_level,
        compression=_compression_type
    )

def set_colors() -> None:
    logger.level("TRACE",color = "<magenta>")
    logger.level("DEBUG",color = "<cyan>")
    logger.level("INFO",color = "<blue>")
    logger.level("SUCCESS",color = "<green>")
    logger.level("WARNING",color = "<yellow>")
    logger.level("ERROR",color = "<red>")
    logger.level("CRITICAL",color = "<b><RED><white>")