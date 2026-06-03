import logging
from werkzeug.exceptions import HTTPException
from flask import Flask, request, jsonify
from src.utils.logger import logger, RouteFilter
from src.utils.configer import init_config_section, read_config

default_value = {
    'name': __name__,
    'host': '0.0.0.0',
    'threaded': True,
    'port': 8080,
    'test_port': 8081,
}
init_config_section('global', 'app', default_value)
config = read_config('global')


app = Flask(config.get('app', 'name'))
app.json.ensure_ascii = False  # 支持浏览器中文显示


# ————————————————————————————————————————————全局异常处理————————————————————————————————————————————————————————————

@app.errorhandler(Exception)  
def handle_global_exception(e):  
    # 1️⃣ HTTP 异常（404 / 405 / 403 等）
    if isinstance(e, HTTPException):
        status_code = e.code or 500
        error_message = e.description

        logger.warning(
            f"status_code: {status_code}, error_message: {error_message}"
        )

        response = {
            "success": False,
            "error": {
                "type": e.__class__.__name__,
                "message": error_message,
            },
            "status_code": status_code,
            "path": request.path,
            "method": request.method
        }
    # 服务内部异常，返回 500 状态码  
    else:
        status_code = 500  
        error_message = str(e)
        logger.error(f"status_code: {status_code}, error_message: {error_message}", exc_info=True)
        # 构造统一的错误响应  
        response = {  
            "success": False,  
            "error": {  
                "type": e.__class__.__name__,  # 异常类型  
                "message": error_message,      # 异常信息  
            },  
            "status_code": status_code,  
            "path": request.path,             # 请求路径  
            "method": request.method          # 请求方法  
        }
    return jsonify(response), status_code  


# ————————————————————————————————————————————路由实现————————————————————————————————————————————————————————————

@app.route('/')
def test_route():
    return jsonify({"success": True, "message": "server works!"})


# ————————————————————————————————————————————启动服务————————————————————————————————————————————————————————————

# 添加过滤器到werkzeug日志
werkzeug_logger = logging.getLogger('werkzeug')
route_filter = RouteFilter([])
werkzeug_logger.addFilter(route_filter)

# 启动服务
host = config.get('app', 'host')
threaded = config.getboolean('app', 'threaded')
env = config.get('global', 'env')
if env == 'production':
    port = config.getint('app', 'port')
else:
    port = config.getint('app', 'test_port')

app.run(host=host, port=port, threaded=threaded)