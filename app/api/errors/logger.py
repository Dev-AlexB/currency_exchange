import logging


def setup_logger():
    logger = logging.getLogger("currency_app")
    logger.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    template = "%(asctime)s - %(levelname)s - [Файл: %(filename)s, Номер строки: %(lineno)s]: %(message)s"
    formatter = logging.Formatter(template)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    return logger


logger = setup_logger()
