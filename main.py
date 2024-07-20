from classes.logger import LoggerHandler
from time import sleep

if __name__ == '__main__':
    logger = LoggerHandler("discord", "logs")

    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message" + "\n\t" + 'a' * 10)
    logger.critical("This is a critical message")

    logger.set_trace_level()

    while True:
        logger.debug("This is a debug message")
        logger.trace("This is a trace message" + "\n\t" + "5 minutes till next loop")
        sleep(300)
