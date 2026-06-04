from src.utils.requests_client import requests_client
from src.utils.configer import *
config_name = 'apis'

default_value = {
    'api_key': '',
    'base_url': 'http://192.168.6.198:10010',
    'default_model': 'Qwen3-VL-8B-Instruct',
}
required_fields = ['api_key']
init_config_section(config_name, 'model_scheduler', default_value, required_fields)
config = read_config(config_name)

api_key = config.get('model_scheduler', 'api_key')
base_url = config.get('model_scheduler', 'base_url')
default_model = config.get('model_scheduler', 'default_model')

inference_url = base_url + '/inference'
def inference(messages: list[dict], model_name=None, timeout=None, orgin_result=False) -> str:
    if model_name is None:
        model_name = default_model
    url = inference_url

    body = {
        "model_name": model_name,
        "api_key": api_key,
        "timeout": timeout,
        "input": {
            "messages": messages
        }
    } 
    response = requests_client.post(url, json=body, timeout=timeout)
    result = response.json()
    if orgin_result:
        return result
    if 'candidates' in result:
        text = result['candidates'][0]['content']['parts'][0]['text']
    elif 'choices' in result:
        text = result['choices'][0]['message']['content']
    elif 'result' in result:
        text = result['result']
    return text