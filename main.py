from time import sleep

from logs import LoggerHandler

if __name__ == '__main__':
    logger = LoggerHandler()
    logger.info("info message")
    logger.warning("warning message")
    logger.error("error message")
    logger.critical("critical message")

    logger.enable_debug_mode()
    logger.debug("debug message")
    logger.disable_debug_mode()

    logger.enable_trace_mode()
    while True:
        logger.trace("trace message")
        sleep(10)

