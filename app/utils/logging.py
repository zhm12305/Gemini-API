import logging
from datetime import datetime
from collections import deque
from threading import Lock

DEBUG = False  # 可以从环境变量中获取

LOG_FORMAT_DEBUG = '%(asctime)s - %(levelname)s - [%(key)s]-%(request_type)s-[%(model)s]-%(status_code)s: %(message)s - %(error_message)s'
LOG_FORMAT_NORMAL = '[%(asctime)s] [%(levelname)s] [%(key)s]-%(request_type)s-[%(model)s]-%(status_code)s: %(message)s'

# Vertex日志格式
VERTEX_LOG_FORMAT_DEBUG = '%(asctime)s - %(levelname)s - [%(vertex_id)s]-%(operation)s-[%(status)s]: %(message)s - %(error_message)s'
VERTEX_LOG_FORMAT_NORMAL = '[%(asctime)s] [%(levelname)s] [%(vertex_id)s]-%(operation)s-[%(status)s]: %(message)s'

# 配置 logger
logger = logging.getLogger("my_logger")
logger.setLevel(logging.DEBUG)

# 控制台处理器
console_handler = logging.StreamHandler() 

# 设置日志格式
console_formatter = logging.Formatter('%(message)s')
console_handler.setFormatter(console_formatter) 
logger.addHandler(console_handler)

# 日志缓存，用于在网页上显示最近的日志
class LogManager:
    def __init__(self, max_logs=100):
        self.logs = deque(maxlen=max_logs)  # 使用双端队列存储最近的日志
        self.lock = Lock()
    
    def add_log(self, log_entry):
        with self.lock:
            self.logs.append(log_entry)
    
    def get_recent_logs(self, count=50):
        with self.lock:
            return list(self.logs)[-count:]

# 创建日志管理器实例 (输出到前端)
log_manager = LogManager()

# Vertex日志缓存，用于在网页上显示最近的Vertex日志
class VertexLogManager:
    def __init__(self, max_logs=100):
        self.logs = deque(maxlen=max_logs)  # 使用双端队列存储最近的Vertex日志
        self.lock = Lock()
    
    def add_log(self, log_entry):
        with self.lock:
            self.logs.append(log_entry)
    
    def get_recent_logs(self, count=50):
        with self.lock:
            return list(self.logs)[-count:]

# 创建Vertex日志管理器实例 (输出到前端)
vertex_log_manager = VertexLogManager()

def format_log_message(level, message, extra=None):
    extra = extra or {}
    log_values = {
        'asctime': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'levelname': level,
        'key': extra.get('key', ''),
        'request_type': extra.get('request_type', ''),
        'model': extra.get('model', ''),
        'status_code': extra.get('status_code', ''),
        'error_message': extra.get('error_message', ''),
        'message': message
    }
    log_format = LOG_FORMAT_DEBUG if DEBUG else LOG_FORMAT_NORMAL
    formatted_log = log_format % log_values
    
    # 将格式化后的日志添加到日志管理器
    log_entry = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'level': level,
        'key': extra.get('key', ''),
        'request_type': extra.get('request_type', ''),
        'model': extra.get('model', ''),
        'status_code': extra.get('status_code', ''),
        'message': message,
        'error_message': extra.get('error_message', ''),
        'formatted': formatted_log
    }
    log_manager.add_log(log_entry)
    
    return formatted_log

def vertex_format_log_message(level, message, extra=None):
    extra = extra or {}
    log_values = {
        'asctime': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'levelname': level,
        'vertex_id': extra.get('vertex_id', ''),
        'operation': extra.get('operation', ''),
        'status': extra.get('status', ''),
        'error_message': extra.get('error_message', ''),
        'message': message
    }
    log_format = VERTEX_LOG_FORMAT_DEBUG if DEBUG else VERTEX_LOG_FORMAT_NORMAL
    formatted_log = log_format % log_values
    
    # 将格式化后的Vertex日志添加到Vertex日志管理器
    log_entry = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'level': level,
        'vertex_id': extra.get('vertex_id', ''),
        'operation': extra.get('operation', ''),
        'status': extra.get('status', ''),
        'message': message,
        'error_message': extra.get('error_message', ''),
        'formatted': formatted_log
    }
    vertex_log_manager.add_log(log_entry)
    
    return formatted_log
    
    
def log(level: str, message: str, extra: dict = None, **kwargs):
    final_extra = {}
    
    if extra is not None and isinstance(extra, dict):
        final_extra.update(extra)
    
    # 将 kwargs 中的其他关键字参数合并进来，kwargs 会覆盖 extra 中的同名键
    final_extra.update(kwargs)
    
    # 调用 format_log_message，传递合并后的 final_extra 字典
    msg = format_log_message(level.upper(), message, extra=final_extra)
    
    getattr(logger, level.lower())(msg)

def vertex_log(level: str, message: str, extra: dict = None, **kwargs):
    final_extra = {}
    
    if extra is not None and isinstance(extra, dict):
        final_extra.update(extra)
    
    # 将 kwargs 中的其他关键字参数合并进来，kwargs 会覆盖 extra 中的同名键
    final_extra.update(kwargs)
    
    # 调用 vertex_format_log_message，传递合并后的 final_extra 字典
    msg = vertex_format_log_message(level.upper(), message, extra=final_extra)
    
    getattr(logger, level.lower())(msg)