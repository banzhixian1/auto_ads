import argparse
from configparser import ConfigParser
import json
import os
from pathlib import Path

from src.prompts.relevance import build_relevance_messages


API_KEY_ENV = "MODEL_SCHEDULER_API_KEY"
DEFAULT_API_KEY = "sk_l8GvFNXK5unhhGrap9rJjwxj6HHXFLse"
DEFAULT_BASE_URL = "http://192.168.6.198:10010"
DEFAULT_MODEL = "Qwen3-VL-8B-Instruct"
DEFAULT_OUTPUT_DIR = Path("debug_relevance_llm_outputs")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run relevance prompt test with LLM.")
    parser.add_argument("--api-key", default=None, help=f"默认读取环境变量 {API_KEY_ENV}")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--no-image", action="store_true", help="不传商品图片，只用文本 prompt。")
    parser.add_argument("--origin-result", action="store_true", help="保存模型接口原始返回。")
    return parser.parse_args()


def resolve_api_key(args: argparse.Namespace) -> str:
    api_key = args.api_key or os.environ.get(API_KEY_ENV, "") or DEFAULT_API_KEY
    api_key = api_key.strip()
    if not api_key:
        raise ValueError(f"缺少 API Key。请传 --api-key，或设置环境变量 {API_KEY_ENV}。")
    return api_key


def ensure_llm_config(base_url: str, model: str) -> None:
    """
    src.apis.llm 导入时会读取 configs/apis.ini。
    这里只写非敏感占位值，真实 key 在运行时注入模块变量。
    """
    config_path = Path("configs") / "apis.ini"
    config_path.parent.mkdir(parents=True, exist_ok=True)

    config = ConfigParser()
    if config_path.exists():
        config.read(config_path, encoding="utf-8")

    section = "model_scheduler"
    if section not in config:
        config.add_section(section)

    config.set(section, "api_key", "runtime")
    config.set(section, "base_url", base_url.rstrip("/"))
    config.set(section, "default_model", model)

    with config_path.open("w", encoding="utf-8") as file:
        config.write(file)


def write_json(path: Path, value) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_result(output_dir: Path, result, origin_result: bool) -> Path:
    if origin_result or isinstance(result, (dict, list)):
        result_path = output_dir / "relevance_llm_origin_result.json"
        write_json(result_path, result)
        return result_path

    try:
        parsed = json.loads(result)
    except (TypeError, json.JSONDecodeError):
        result_path = output_dir / "relevance_llm_result.txt"
        result_path.write_text(str(result), encoding="utf-8")
        return result_path

    result_path = output_dir / "relevance_llm_result.json"
    write_json(result_path, parsed)
    return result_path


def run() -> tuple[Path, Path]:
    args = parse_args()
    api_key = resolve_api_key(args)
    base_url = args.base_url.rstrip("/")
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    ensure_llm_config(base_url=base_url, model=args.model)

    from src.apis import llm as llm_api

    llm_api.api_key = api_key
    llm_api.base_url = base_url
    llm_api.default_model = args.model
    llm_api.inference_url = f"{base_url}/inference"

    messages = build_relevance_messages(include_image=not args.no_image)
    messages_path = output_dir / "relevance_llm_messages.json"
    write_json(messages_path, messages)

    result = llm_api.inference(
        messages=messages,
        model_name=args.model,
        timeout=args.timeout,
        orgin_result=args.origin_result,
    )
    result_path = write_result(output_dir, result, args.origin_result)
    return messages_path, result_path


def main() -> None:
    messages_path, result_path = run()
    print(f"Wrote {messages_path}")
    print(f"Wrote {result_path}")


if __name__ == "__main__":
    main()
