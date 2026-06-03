import requests
import json
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.utils.configer import *
config_name = 'requests'
default_value = {
    'retries': 5,
    'backoff_factor': 2,
    'timeout': 60,
    'status_forcelist': json.dumps([]),
}
init_config_section(config_name, 'requests_client', default_value)
config = read_config(config_name)

class RequestsClient:
    def __init__(
        self,
        retries: int = config.getint('requests_client', 'retries'),
        backoff_factor: float = config.getfloat('requests_client', 'backoff_factor'),
        timeout: int = config.getint('requests_client', 'timeout'),
        status_forcelist: list = json.loads(config.get('requests_client', 'status_forcelist')),
    ):
        self.timeout = timeout
        self.session = requests.Session()

        retry_strategy = Retry(
            total=retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
            allowed_methods=["GET", "POST", "PUT", "DELETE"],
            raise_on_status=False,
            raise_on_redirect=False,
            connect=0,  # 连接超时不重试
            read=0,  # 读取超时不重试
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _request(self, method, url, **kwargs):
        """内部统一请求封装，记录日志"""
        try:
            timeout = kwargs.pop("timeout", self.timeout)
            response = self.session.request(method, url, timeout=timeout, **kwargs)
            response.raise_for_status()
            return response

        except requests.exceptions.HTTPError as e:
            response = e.response
            try:
                detail = response.json()
            except ValueError:
                detail = response.text

            e.args = (
                f"{method.upper()} {url} failed: {detail}",
            )
            raise


    # 对外暴露方法
    def get(self, url, **kwargs):
        return self._request("GET", url, **kwargs)

    def post(self, url, **kwargs):
        return self._request("POST", url, **kwargs)
    
    def put(self, url, **kwargs):
        return self._request("PUT", url, **kwargs)
    
    def delete(self, url, **kwargs):
        return self._request("DELETE", url, **kwargs)
    
    def patch(self, url, **kwargs):
        return self._request("PATCH", url, **kwargs)

requests_client = RequestsClient()

# 带 token 刷新的请求客户端
class RequestsTokenClient(RequestsClient):
    def __init__(
            self, 
            refresh_token_func: callable,
            check_token_error_func: callable,
            check_response_error_func: callable,
            token_refresh_status: tuple = (),
            business_error_codes: tuple = (),
            retries: int = config.getint('requests_client', 'retries'),
            backoff_factor: float = config.getfloat('requests_client', 'backoff_factor'),
            timeout: int = config.getint('requests_client', 'timeout'),
            status_forcelist: list = json.loads(config.get('requests_client', 'status_forcelist')),
        ):
        """
        带 token 刷新的请求客户端
        :param refresh_token_func: 刷新 token 的函数，该函数需要返回新的 kwargs
        :param check_token_error_func: 检查 token 是否过期的函数，该函数需要返回 True 表示过期
        :param check_response_error_func: 检查响应是否为业务错误的函数，该函数需要返回 True 表示为业务错误
        :param token_refresh_status: token 过期时的状态码，默认值为空元组
        :param business_error_codes: 业务错误码，默认值为空元组
        :param retries: 最大重试次数
        :param backoff_factor: 重试间隔因子
        :param timeout: 请求超时时间
        :param status_forcelist: 强制重试的状态码列表，默认值为空列表
        """
        super().__init__(retries, backoff_factor, timeout, status_forcelist)
        self._refresh_token = refresh_token_func
        self._check_token_error = check_token_error_func
        self._check_response_error = check_response_error_func
        self.token_refresh_status: tuple = token_refresh_status
        self.business_error_codes: tuple = business_error_codes
        self.retries = retries
        self.backoff_factor = backoff_factor
        self.timeout = timeout

        self.url_retries_list: list = []

    def _check_token_error(response: requests.Response) -> bool:
        """检查token是否过期， True 表示过期，该方法由外部注入"""
        pass

    def _check_response_error(response: requests.Response) -> bool:
        """检查响应是否为业务错误， True 表示为业务错误, 该方法由外部注入"""
        pass

    def _refresh_token(self, kwargs: dict) -> dict:
        """刷新 Access Token，更新 kwargs 中的 headers，该方法由外部注入"""
        pass
        # 实现参考  
        # access_token = self._get_access_token()
        # self.access_token = access_token
        # headers = kwargs.get('headers') or {}
        # headers['Access-Token'] = access_token  # 请根据headers的具体access_token字段名进行赋值
        # kwargs['headers'] = headers
        # return kwargs
    
    def _request_agent_no_intercept(self, method, url, *args, **kwargs):
        """不拦截业务码，只处理 token 过期自动刷新"""
        response = self.session.request(method, url, *args, **kwargs)

        # 检查 token 是否过期
        if not self._check_token_error(response):
            return response
        # 刷新 token 并更新 kwargs
        kwargs = self._refresh_token(kwargs)
        # 重试一次请求
        response = self.session.request(method, url, *args, **kwargs)
        return response
        
    def _response_retries(self, method, url, *args, **kwargs):
        retries = 1
        while retries <= self.retries:
            response = self._request_agent_no_intercept(method, url, *args, **kwargs)
            if not self._check_response_error(response):
                return response

            delay = self.backoff_factor * (2 ** (retries - 1))
            time.sleep(delay)
            retries += 1

        raise Exception(f"[RETRY] {method.upper()} {url} failed after {self.retries} retries.")

    def _request_agent(self, method, url, *args, **kwargs):
        """请求入口（带重试 + token 刷新）"""
        if url in self.url_retries_list:
            raise Exception(f"{url} 正在重试中, 请稍后重试")

        # 第一次直接请求
        response = self._request_agent_no_intercept(method, url, *args, **kwargs)
        if self._check_response_error(response): # 如果业务错误，进入重试流程
            # self.url_retries_list.append(url)  # 可根据实际情况是否需要添加到重试列表
            response = self._response_retries(method, url, *args, **kwargs)
            # self.url_retries_list.remove(url)

        # 最终仍然不成功
        if self._check_response_error(response):
            raise Exception(f"[BUSINESS ERROR] {method.upper()} {url}")
        return response
    
    # 对外暴露方法
    def get(self, url, **kwargs):
        return self._request_agent("GET", url, **kwargs)

    def post(self, url, **kwargs):
        return self._request_agent("POST", url, **kwargs)
    
    def put(self, url, **kwargs):
        return self._request_agent("PUT", url, **kwargs)
    
    def delete(self, url, **kwargs):
        return self._request_agent("DELETE", url, **kwargs)

    def patch(self, url, **kwargs):
        return self._request_agent("PATCH", url, **kwargs)