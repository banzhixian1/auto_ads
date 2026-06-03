from pathlib import Path
import logging
import json
from jsonschema import Draft202012Validator
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------LLM------------------------------------------------------

def type_check(text: str, type_name: str, messages: list, logger: logging.Logger = None) -> tuple[bool, list]:
    """
    检查字符串是否为指定类型
    :param text: 需要检查的字符串
    :param type_name: 类型名称，如 'int', 'float', 'str' 等
    :param messages: 用于记录对话的消息列表
    :return: 元组，第一个元素为是否符合要求，第二个元素为更新后的messages
    """
    if logger:
        logger.debug(f"text: {text}")
    try:
        if type_name == 'int':
            int(text)
        elif type_name == 'float':
            float(text)
        else:
            raise ValueError(f"不支持的类型名称: {type_name}")
        return True, messages
    except ValueError:
        messages.append({
            "role": "assistant",
            "content": [
                {"type": "text", "text": text}
            ]
        })
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": f'"{text}" 不是 {type_name} 类型，请重新生成'}
            ]
        })
        return False, messages

def enum_check(text: str, enum_list: list[str], messages: list = None, logger: logging.Logger = None) -> tuple[bool, list]:
    """
    检查字符串是否在枚举列表中
    :param text: 需要检查的字符串
    :param enum_list: 枚举值列表
    :param messages: 用于记录对话的消息列表
    :return: 元组，第一个元素为是否符合要求，第二个元素为更新后的messages
    """
    if messages is None:
        messages = []
    if logger:
        logger.debug(f"text: {text}")
    if text in enum_list:
        return True, None

    messages.append({
        "role": "assistant",
        "content": [
            {"type": "text", "text": text}
        ]
    })
    messages.append({
        "role": "user",
        "content": [
            {"type": "text", "text": f'"{text}" 不在 {enum_list} 中，请检查字符是否完全一致。重新生成'}
        ]
    })
    return False, messages

def schema_check(text: str, schema: dict, messages: list = None, logger: logging.Logger = None) -> tuple[bool, list]:
    """
    检查json字符串是否符合schema要求
    """
    if messages is None:
        messages = []
    try:
        messages.append({
            "role": "assistant",
            "content": [{"type": "text", "text": text}]
        })
        json_obj = json.loads(text)
        if logger:
            logger.debug(f"json_obj: {json_obj}")

        # 逐条收集错误，并使用更可读的形式
        validator = Draft202012Validator(schema)
        errors = sorted(validator.iter_errors(json_obj), key=lambda e: e.path)

        if errors:
            # 提取所有错误（但简化为用户可读格式）
            error_msgs = []
            for err in errors:
                field = ".".join(str(p) for p in err.path) or "(root)"
                error_msgs.append(f"{field}: {err.message}")

            joined = "\n".join(error_msgs)
            if logger:
                logger.debug(f"错误信息：{joined}")

            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"生成的 JSON 不符合 schema 要求：\n{joined}\n请重新生成符合 schema 的 JSON。"
                    }
                ]
            })

            return False, messages
        # 没有错误
        return True, messages

    except json.JSONDecodeError as e:
        # JSON 语法错误
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": f"JSON 格式错误：{e}，请重新生成合法 JSON。"}
            ]
        })
        return False, messages
    

class GenerationRetryError(Exception):
    """生成重试失败异常"""
    def __init__(self, max_retry: int, messages: list[dict] = None):
        self.max_retry = max_retry
        self.messages = messages
        super().__init__(f"生成函数在 {max_retry} 次重试后仍然失败")

def generate_with_retry(messages:list[dict], generate_func: callable, check_func: callable, max_retry: int = 5, logger: logging.Logger = None) -> str:
    """
    带校验重试的生成函数，直到符合检查函数的要求或达到最大重试次数  
    :param generate_func: 生成函数，输入messages，返回模型生成结果字符串  
    :param check_func: 检查函数，输入需要检查字符串和messages，返回元组，第一个元素为是否符合要求，第二个元素为更新后的messages  
    :param max_retry: 最大重试次数，默认5次  
    :param logger: 日志记录器，默认None  
    :return: 符合检查函数要求的字符串
    """
    for _ in range(max_retry):
        response = generate_func(messages = messages)
        result, messages = check_func(text = response, messages = messages, logger = logger)
        if result:
            return response
        if logger:
            logger.debug(f"generate_func failed, retry {_+1} times, messages: {messages[1:]}")
    if logger:
        logger.warning(f"generate_func failed after {max_retry} times, messages: {messages[1:]}")
    raise GenerationRetryError(max_retry, messages)


# ---------------------------------------IMAGE------------------------------------------------------

def resize_with_aspect_ratio(image: Image.Image, max_size: int) -> Image.Image:
    """
    按比例缩放图片，最长边不超过 max_size
    """
    w, h = image.size
    if max(w, h) <= max_size:
        return image  # 不需要缩放
    
    if w > h:
        new_w = max_size
        new_h = int(h * max_size / w)
    else:
        new_h = max_size
        new_w = int(w * max_size / h)
    
    return image.resize((new_w, new_h), Image.Resampling.LANCZOS)