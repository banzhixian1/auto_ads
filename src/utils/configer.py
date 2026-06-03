import os
from configparser import ConfigParser

from src.utils.utils import ROOT
config_directory = ROOT / 'configs'

def read_config(config_name: str):
    config = ConfigParser()
    config_path = os.path.join(config_directory, f'{config_name}.ini')
    config.read(config_path, encoding='utf-8')
    return config

def save_config(config: ConfigParser, config_name: str):
    """保存当前配置到文件"""
    try:
        config_path = os.path.join(config_directory, f'{config_name}.ini')
        # 确保目录存在
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        # 使用临时文件写入，避免写入过程中出错导致原文件损坏
        temp_path = config_path + '.tmp'
        with open(temp_path, 'w', encoding='utf-8') as f:
            config.write(f)
        
        # 原子性替换原文件
        if os.path.exists(config_path):
            os.replace(temp_path, config_path)
        else:
            os.rename(temp_path, config_path)
            
    except Exception as e:
        print(f"保存配置文件失败: {e}")
        # 删除可能残留的临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)

from typing import Any

def init_config_section(
    config_name: str,
    section: str,
    defaults: dict[str, Any],
    required_fields: list[str] | None = None
):
    """初始化ini配置节和默认值，必填字段缺失会抛异常
    :param config_name: 配置文件名（不带扩展名）
    :param section: 配置节名称
    :param defaults: 配置节默认值字典
    :param required_fields: 必填字段列表，默认 None"""
    config = read_config(config_name)

    if section not in config:
        config.add_section(section)

    if required_fields is None:
        required_fields = []
    missing_fields = []

    change = False
    for key, value in defaults.items():
        if key not in config[section]:
            if key in required_fields:
                missing_fields.append(key)
            config.set(section, key, str(value))
            change = True
    if change:
        save_config(config, config_name)
    if missing_fields:
        raise ValueError(f"配置文件 '{config_name}' 配置节 '{section}' 缺少必填字段: {', '.join(missing_fields)}")

config_name = 'global'
default_value = {  # 全局配置的默认值
    "env": "development",  # 运行环境，development 或 production
}
init_config_section(config_name, 'global', default_value)
global_config = read_config(config_name)

__all__ = [
    "read_config",
    "init_config_section",
    "global_config",
]