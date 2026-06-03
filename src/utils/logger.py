import logging
from logging.handlers import TimedRotatingFileHandler
import os
from pathlib import Path
import shutil
from src.utils.configer import *
from src.utils.utils import ROOT
config_name = 'logger'
default_value = {
    'log_file': 'ROOT/logs/project.log',
    'log_level': 'INFO',
}
init_config_section(config_name, 'logger', default_value)
config = read_config(config_name)

log_file = config.get('logger', 'log_file')
if log_file.startswith('ROOT'):
    log_file = log_file.replace('ROOT', str(ROOT))
Path(log_file).parent.mkdir(parents=True, exist_ok=True)
logger = logging.getLogger("materialProcess")

log_level = config.get('logger', 'log_level')
if log_level.upper() == "DEBUG":
    logger.setLevel(logging.DEBUG)
elif log_level.upper() == "WARNING":
    logger.setLevel(logging.WARNING)
elif log_level.upper() == "ERROR":
    logger.setLevel(logging.ERROR)
else:
    logger.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
file_handler = TimedRotatingFileHandler(
    log_file,
    when="midnight",
    backupCount=3650,
    encoding="utf-8"
)
file_handler.setFormatter(formatter)

def custom_namer(default_name):
    base, date = default_name.rsplit(".", 1)
    return f"{base}.{date}.log"

file_handler.namer = custom_namer

def safe_rotate(self, source, dest):
    """
    覆盖原 rotate，实现 Windows 兼容的重命名。
    保持调用 rotator 的行为不变，默认重命名时捕获异常并 fallback。
    """
    if not callable(self.rotator):
        if os.path.exists(source):
            try:
                os.rename(source, dest)
            except PermissionError:
                try:
                    shutil.copy2(source, dest)
                    with open(source, "w", encoding="utf-8"):
                        pass
                except Exception:
                    pass
    else:
        self.rotator(source, dest)
        
file_handler.rotate = safe_rotate.__get__(file_handler, type(file_handler))

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

if not logger.hasHandlers():
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


# 路由日志过滤器
import re
import logging
class RouteFilter(logging.Filter):
    def __init__(self, excluded_routes: list[str], excluded_codes: set[int] = None):
        '''
        过滤werkzeug日志，排除指定路由的日志
        :param excluded_routes: 要排除的路由列表
        :param excluded_codes: 要排除的状态码集合，默认值为{ 200, 206, 304 }
        '''
        super().__init__()
        self.excluded_routes = excluded_routes
        if excluded_codes is None:
            excluded_codes = { 200, 206, 304 }
        self.excluded_codes = excluded_codes
    
        self.pattern = re.compile(r'"[A-Z]+ (?P<path>\S+) HTTP/[\d.]+" (?P<status>\d{3})')
        self.ansi_escape = re.compile(r'\x1b\[[0-9;]*m')

    def extract_path_and_status(self, log_message):
        log_message = self.ansi_escape.sub('', log_message)
        match = self.pattern.search(log_message)
        if match:
            path = match.group('path')      # '/static/file.js'
            status = int(match.group('status'))  # 200
            return path, status
        else:
            raise ValueError("Log message does not match expected format")

    def filter(self, record):
        message = record.getMessage()
        try:
            path, status = self.extract_path_and_status(message)
        except ValueError:
            return True
        # 检查日志消息是否包含要过滤的路由
        if status not in self.excluded_codes:
            return True
        for route in self.excluded_routes:
            if path.startswith(route):
                return False
        return True