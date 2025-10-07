"""
配置管理模块
支持多语言和用户自定义配置
"""

import os
from pathlib import Path
import json
import locale

CONFIG_FILE = Path.home() / '.aiworktracker' / 'config.json'


def get_default_language():
    """自动检测系统语言"""
    try:
        lang, _ = locale.getdefaultlocale()
        if lang:
            if lang.startswith('zh'):
                return 'zh'
            elif lang.startswith('ja'):
                return 'ja'
        return 'en'
    except:
        return 'en'


def get_config():
    """获取用户配置"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    
    # 返回默认配置
    return {
        'language': get_default_language(),
        'openai_model': os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    }


def save_config(config):
    """保存用户配置"""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, fp=f, indent=2, ensure_ascii=False)


def get_language():
    """获取当前语言设置"""
    config = get_config()
    return config.get('language', 'zh')


def set_language(language):
    """设置语言"""
    if language not in ['zh', 'en', 'ja']:
        raise ValueError(f"不支持的语言: {language}")
    
    config = get_config()
    config['language'] = language
    save_config(config)
