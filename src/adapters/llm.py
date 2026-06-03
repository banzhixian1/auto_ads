import copy
from PIL.Image import Image
from src.adapters.image import decode_image, image_to_base64
from src.utils.utils import resize_with_aspect_ratio
from src.utils.requests_client import requests_client

def _replace_images_in_parts(parts: list[dict], mark = False) -> list[dict]:
    for part in parts:
        if not isinstance(part, dict):
            continue

        if 'thoughtSignature' in part:
            thought_signature = part['thoughtSignature']
            if thought_signature.startswith("http"):
                response = requests_client.get(thought_signature)
                result = response.json()
                if result.get("success") == True:
                    part['thoughtSignature'] = result["thought_signature"]
                else:
                    error_message = result.get("message", "未知错误")
                    raise RuntimeError(f"思考签名获取失败: {error_message}")

        if 'functionResponse' in part:
            function_response = part['functionResponse']
            if 'parts' in function_response and isinstance(function_response['parts'], list):
                _replace_images_in_parts(function_response['parts'])
                continue

        if 'inline_data' not in part:
            continue

        inline_data = part["inline_data"]

        if "data" not in inline_data:
            continue

        image_str = inline_data["data"]

        if not isinstance(image_str, str):
            continue

        if inline_data.get('_is_processed', False):
            continue

        # 调用 decode_image
        image = decode_image(image_str)
        if not isinstance(image, Image):
            raise ValueError("decode_image did not return PIL.Image.Image")
        image = resize_with_aspect_ratio(image, 1920)
        image_base64 = image_to_base64(image)
        inline_data["data"] = image_base64
        if mark:
            inline_data['_is_processed'] = True  # 标记这个图片已经被处理过了，避免重复处理

def replace_images_in_contents(contents: list[dict]) -> list[dict]:
    """
    遍历 contents，把所有 inline_data 字段用 encode_image_Base64 编码为 base64 image/png 字符串
    :param contents: 标准 gemini contents 列表
    """
    for content in contents:
        if "parts" not in content:
            continue

        parts = content["parts"]

        if not isinstance(parts, list):
            continue

        _replace_images_in_parts(parts)

    return contents

def _remove_mask_in_parts(parts: list[dict]):
    """递归移除 parts 中所有 blob 里的私有标记位"""
    for part in parts:
        if not isinstance(part, dict):
            continue

        # 1. 递归处理 functionResponse 内部的 parts
        if 'functionResponse' in part:
            function_response = part['functionResponse']
            if 'parts' in function_response and isinstance(function_response['parts'], list):
                _remove_mask_in_parts(function_response['parts'])
            continue

        # 2. 移除当前 part 中 blob 的标记位 (兼容两种字段名)
        blob = part.get("inline_data") or part.get("inlineData")
        if isinstance(blob, dict) and "_is_processed" in blob:
            del blob["_is_processed"]

def remove_mask_in_contents(contents: list[dict]) -> list[dict]:
    """
    深度拷贝并清理所有内部标记，返回一个可以安全发送给 API 的纯净对象
    """
    # 必须 deepcopy，否则会把内存中用来防止重复编码的标记位给删了
    clean_contents = copy.deepcopy(contents)
    
    for content in clean_contents:
        parts = content.get("parts")
        if isinstance(parts, list):
            _remove_mask_in_parts(parts)
            
    return clean_contents

def messages_to_contents(messages: list[dict], image_key: str = "image") -> list[dict]:
    """
    把 openai messages 转换为 gemini contents 格式
    :param messages: openai messages 列表
    messages: [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "image": "https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen-VL/assets/demo.jpeg",
                    "thoughtSignature": "thoughtSignature"
                },
                {
                    "type": "text", 
                    "text": "Describe this image."
                },
            ],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "text", 
                    "text": "This is a demo image."
                }
            ],
    ]
    :param image_key: 图片类型的 key，默认是 "image"
    :return: 标准 gemini contents 列表
    contents: [
        {
            "role": "user",
            "parts": [
                {"text": "An office group photo of these people, they are making funny faces."},
                {"inline_data": {"mime_type":"image/png", "data": "https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen-VL/assets/demo.jpeg"}},
            ]
        },
        {
            "role": "model",
            "parts": [
                {
                    "inline_data": {"mime_type": "image/png", "data": "<PREVIOUS_IMAGE_DATA>"}},
                    "thoughtSignature": "thoughtSignature"
                }
            ]
        },
    ],
    """
    
    gemini_contents = []
    for message in messages:
        role = message.get("role", "user")
        if role == "assistant":
            role = "model"
        elif role == "system":
            role = "user"
        gemini_content = {
            "role": role,
            "parts": []
        }
        if "content" not in message:
            continue
        contents = message["content"]
        for content in contents:
            if isinstance(content, dict):
                if "type" not in content:
                    continue
                if content["type"] == image_key:
                    part = {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": content[image_key]
                        }
                    }
                elif content["type"] == "text":
                    part = {
                        "text": content.get("text", "")
                    }
                else:
                    continue
                if content.get("thoughtSignature") is not None:
                    part["thoughtSignature"] = content["thoughtSignature"]
            elif isinstance(content, str):
                part = {
                    "text": content
                }
            else:
                continue

            gemini_content["parts"].append(part)

        if gemini_content["parts"]:
            gemini_contents.append(gemini_content)

    return gemini_contents