import logging
import colorlog


class LoggerHandler:

    def __init__(self, log_file_info="logs/bot.log", log_file_error="logs/bot.err", color=True):

        dateformat = "[%d/%m/%Y %H:%M:%S]"

        log_format = "%(levelname)s %(asctime)s - %(message)s"
        log_formatter = logging.Formatter(log_format, datefmt=dateformat)

        console_format_colored = "%(white)s%(asctime)s %(log_color)s%(levelname)-8s%(reset)s : %(white)s%(message)s"

        self.logger = colorlog.getLogger('discord')

        # Add TRACE level
        logging.addLevelName(logging.DEBUG - 5 , 'TRACE')

        # Write logs to the console
        if color:
            stream_handler = colorlog.StreamHandler()
            stream_handler.setFormatter(colorlog.ColoredFormatter(
                console_format_colored,
                datefmt=dateformat,
                reset=True,
                log_colors={
                    'TRACE': 'light_purple',
                    'DEBUG': 'white',
                    'INFO': 'cyan',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'fg_bold_red,bg_yellow'
                },
                secondary_log_colors={},
                style='%'
            ))
        else:
            console_format = logging.Formatter("%(asctime)s %(levelname)-8s : %(message)s", datefmt=dateformat)
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(console_format)

        self.logger.addHandler(stream_handler)

        # Write logs info to log_file_info
        self.file_handler_info = logging.FileHandler(filename=log_file_info, encoding='utf-8', mode='a+')
        self.file_handler_info.setFormatter(log_formatter)
        self.file_handler_info.setLevel(logging.INFO)

        # don't write errors and criticals to log_file_info
        self.file_handler_info.addFilter(lambda record: record.levelno < logging.ERROR)
        self.logger.addHandler(self.file_handler_info)

        # Write logs error to log_file_error
        self.file_handler_error = logging.FileHandler(filename=log_file_error, encoding='utf-8', mode='a+')
        self.file_handler_error.setFormatter(log_formatter)
        self.file_handler_error.setLevel(logging.ERROR)
        self.logger.addHandler(self.file_handler_error)

        # Logger level
        self.logger.setLevel(logging.INFO)

    def enable_debug_mode(self):
        if self.logger.level > logging.DEBUG:
            self.logger.setLevel(logging.DEBUG)
            self.file_handler_info.setLevel(logging.DEBUG)
            self.logger.info("Debug mode enabled")

    def disable_debug_mode(self):
        if self.logger.level <= logging.DEBUG:
            self.logger.setLevel(logging.INFO)
            self.file_handler_info.setLevel(logging.INFO)
            self.logger.info("Debug mode disabled")

    def enable_trace_mode(self):
        if self.logger.level > logging.DEBUG - 5:
            self.logger.setLevel(logging.DEBUG - 5)
            self.file_handler_info.setLevel(logging.DEBUG - 5)
            self.logger.info("Trace mode enabled")

    def disable_trace_mode(self):
        if self.logger.level <= logging.DEBUG - 5:
            self.logger.setLevel(logging.INFO)
            self.file_handler_info.setLevel(logging.INFO)
            self.logger.info("Trace mode disabled")

    def clear_log(self):
        try:
            with open("logs/bot.log", "w") as f:
                f.write("")
            with open("logs/bot.err", "w") as f:
                f.write("")
            self.logger.info("Logs cleared")
        except FileNotFoundError as e:
            self.logger.error(e)

    def trace(self, message):
        self.logger.log(logging.DEBUG - 5, message)

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)
