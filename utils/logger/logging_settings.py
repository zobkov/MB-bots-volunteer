import sys

logging_config = {
    'version': 1,
    'disable_existing_loggers': False,  # Allow existing loggers to propagate
    'formatters': {
        'formatter_2': {
            'format': '#%(levelname)-8s [%(asctime)s] - %(filename)s:'
                      '%(lineno)d - %(name)s:%(funcName)s - %(message)s'
        }
    },
    'handlers': {
        'stdout': {
            'class': 'logging.StreamHandler',
            'formatter': 'formatter_2',
            'stream': sys.stdout
        }
    },
    'root': {
        'handlers': ['stdout'],
        'level': 'DEBUG'
    },
    'loggers': {
        'aiogram': {  # Configure the aiogram logger
            'handlers': ['stdout'],
            'level': 'DEBUG',
            'propagate': False
        }
    }
}