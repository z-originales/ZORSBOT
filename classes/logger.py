import logging
from logging.handlers import WatchedFileHandler
from colorlog import ColoredFormatter


class UnescapedFormatter(logging.Formatter):

    def __init__(self, fmt=None, datefmt=None, style='%'):
        super().__init__(fmt=fmt, datefmt=datefmt, style=style)

    def format(self, record):
        record.msg = repr(record.getMessage())
        return super().format(record)


class LoggerHandler(logging.Logger):
    _instance = None
    TRACE = 5
    logging.addLevelName(TRACE, "TRACE")

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(LoggerHandler, cls).__new__(cls)
        return cls._instance

    def __init__(self, name, log_dir, console_level=logging.INFO):

        if not hasattr(self, 'is_initialized'):
            super().__init__(name)
            self.setLevel(console_level)
            self.datefmt = "[%d/%m/%Y %H:%M:%S]"
            self.add_console_handler(console_level)
            self.add_file_handlers(log_dir)
            self.is_initialized = True

    def add_console_handler(self, console_level):
        console_handler = logging.StreamHandler()
        console_formatter = ColoredFormatter(
            "%(white)s%(asctime)s %(log_color)s%(levelname)-8s%(reset)s : %(white)s%(message)s",
            datefmt=self.datefmt,
            reset=True,
            log_colors={
                'TRACE': 'fg_bold_blue,bg_white',
                'DEBUG': 'light_purple',
                'INFO': 'cyan',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'fg_bold_red,bg_yellow'
            },
        )
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(console_level)
        self.addHandler(console_handler)

    def add_file_handlers(self, log_dir):
        error_file_handler = self.create_file_handler(f"{log_dir}/errors.log", logging.WARNING)
        info_file_handler = self.create_file_handler(f"{log_dir}/info.log", logging.WARNING, less_than=True)
        self.addHandler(error_file_handler)
        self.addHandler(info_file_handler)

    def create_file_handler(self, file_path, level, less_than=False):
        file_handler = WatchedFileHandler(file_path)
        formatter = UnescapedFormatter("%(asctime)s - %(levelname)s - %(message)s", datefmt=self.datefmt)
        file_handler.setFormatter(formatter)
        if less_than:
            file_handler.addFilter(lambda record: record.levelno < level)
        else:
            file_handler.addFilter(lambda record: record.levelno >= level)
        return file_handler

    # Utility methods

    def set_level(self, level):
        """
        Set the logging level for both the logger and the console handler.

        Args:
            level (int): The logging level (e.g., logging.DEBUG, logging.INFO).
        """
        self.setLevel(level)
        for handler in self.handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.setLevel(level)

    def set_debug_level(self):
        """
        Set the logging level to DEBUG for both the logger and the console handler.
        """
        self.set_level(logging.DEBUG)

    def set_trace_level(self):
        """
        Set the logging level to TRACE for both the logger and the console handler.
        """
        self.set_level(self.TRACE)

    # Custom log methods

    def trace(self, msg, *args, **kwargs):
        """
        Log a message with severity 'TRACE' on this logger.

        Args:
            msg (str): The message to log.
        """
        if self.isEnabledFor(self.TRACE):
            self._log(self.TRACE, msg, args, **kwargs)
