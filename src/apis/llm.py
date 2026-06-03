from src.utils.requests_client import requests_client
from src.utils.configer import *
config_name = 'apis'
default_value = {
    'base_url': 'http://192.168.6.198:10001',
}
init_config_section(config_name, 'local_llm', default_value)
config = read_config(config_name)

def inference(messages: list[dict], model_name='Qwen3-VL-8B-Instruct') -> str:
    if model_name == 'Qwen3-VL-8B-Instruct':
        return local_inference(messages, model_name)
    else:
        raise ValueError(f"model_name {model_name} not supported")

local_llm_url = config.get('local_llm', 'base_url')
def local_inference(messages: list[dict], model_name='Qwen3-VL-8B-Instruct') -> str:
    url = local_llm_url + "/predict"
    body = {
        'model_name': model_name,
        "input": {
            "messages": messages
        }
    }
    try:
        response = requests_client.post(url, json=body, timeout=300)
        return response.json()['result']
    except Exception as e:
        e.args = (
            f"local_inference failed, error={e}, body={body}",
        )
        raise