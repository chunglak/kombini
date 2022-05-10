import logging


def default_logger(logger: logging.Logger = None) -> logging.Logger:
    return logger if logger else get_logger()


def get_logger(
    name: str = None,
    level: str = "info",
    formatter: str = None,
    file: str = None,
    file_level: str = None,
    file_formatter: logging.Formatter = None,
) -> logging.Logger:

    logger = logging.getLogger(name)

    if not len(logger.handlers):
        logger.setLevel("DEBUG")

        if formatter is None:
            formatter = (
                "%(asctime)s-%(module)s[%(funcName)s:%(lineno)s]\n"
                + "%(levelname)s-%(message)s"
            )
        fmt = logging.Formatter(formatter)

        lvl = level.upper()

        ch = logging.StreamHandler()
        ch.setLevel(lvl)
        ch.setFormatter(fmt)
        logger.addHandler(ch)

        if file:
            fh = logging.FileHandler(file)
            fh.setLevel(file_level.upper() if file_level else lvl)
            fh.setFormatter(file_formatter if file_formatter else fmt)
            logger.addHandler(fh)

    return logger
