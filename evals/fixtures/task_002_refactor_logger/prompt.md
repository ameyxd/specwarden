Refactor logger.py so there is a single log(level, message) function and
delete the per-function helpers (debug, info, warn, error, critical). Update
usage.py to call log() with the appropriate level string. Do not change the
actual log messages or the level names.
