from PIL import Image, ImageOps
from io import BytesIO
import base64
from src.utils.requests_client import requests_client

# 图片处理
headers_map = {
    "default": {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "zh-CN,zh;q=0.9",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0"
    },
    "1688": {
        'Referer': 'https://detail.1688.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
}

def load_image_from_url(url: str, headers=None, timeout=60) -> bytes:  
    if headers is None:  
        response = requests_client.get(url, timeout=timeout)  
    else:  
        response = requests_client.get(url, headers=headers, timeout=timeout)  
    return response.content

def try_decode_base64(image_str) -> Image.Image | None:
    try:
        data = base64.b64decode(image_str, validate=True)
        return Image.open(BytesIO(data))
    except Exception:
        return None

def try_https_url(image_str) -> Image.Image:
    try:
        url = 'https://' + image_str
        return Image.open(BytesIO(load_image_from_url(url, headers=headers_map.get("default"))))
    except Exception:
        return None
    
def try_local_path(image_str) -> Image.Image:
    try:
        return Image.open(image_str)
    except Exception:
        return None

def decode_image(image_str: str) -> Image.Image:
    """
    Decode image from various sources into a fully-loaded PIL.Image.

    Supported:
    - http(s) URL
    - data:image/...;base64,...
    - local:/absolute/or/relative/path
    - raw base64

    Guarantees on success:
    - img is fully decoded (img.load() called)
    - EXIF orientation fixed
    - static image (first frame if animated)
    - size sanity-checked
    """
    img: Image.Image = None

    # 1 http / https
    if image_str.startswith("http"):
        headers = headers_map.get("default")
        if "alicdn" in image_str:
            headers = headers_map.get("1688")

        content = load_image_from_url(image_str, headers=headers)
        img = Image.open(BytesIO(content))

    # 2 data URI
    elif image_str.startswith("data:image"):
        _, base64_data = image_str.split(",", 1)
        img = Image.open(BytesIO(base64.b64decode(base64_data)))

    # 3 local file
    elif image_str.startswith("local:"):
        path = image_str[len("local:") :]
        img = Image.open(path)

    # 4 fallback loaders
    else:
        for loader in (try_decode_base64, try_https_url, try_local_path):
            try:
                img = loader(image_str)
            except Exception:
                img = None

            if img is not None:
                break

    if img is None:
        raise ValueError(f"No loader matched any image source: {image_str[:200]}")

    # 5 强制真实解码（避免 lazy error）
    img.load()

    # 6 修正 EXIF 方向
    img = ImageOps.exif_transpose(img)

    # 7 动图处理（取第一帧）
    if getattr(img, "is_animated", False):
        img.seek(0)

    # 8 尺寸校验
    w, h = img.size

    if (w, h) == (1, 1):
        raise ValueError("Image is 1x1 pixel (likely placeholder)")

    if img.mode != "RGB":
        img = img.convert("RGB")  # 避免 RGBA / P 模式问题

    return img
    
def image_to_base64(img: Image.Image) -> str:
    buf = BytesIO()
    img.save(buf, format="PNG")  # 统一 PNG
    return base64.b64encode(buf.getvalue()).decode('utf-8')

def encode_image_Base64(image_str: str) -> str:
    img = decode_image(image_str)
    base64_str = image_to_base64(img)
    return base64_str