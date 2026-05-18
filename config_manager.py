import json
import os

def save_config(filepath: str, data: dict):
    """
    Serializa e salva o dicionário de configuração em JSON.
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_config(filepath: str) -> dict:
    """
    Carrega o JSON e retorna como dicionário.
    Retorna um dicionário vazio se o arquivo não existir ou for inválido.
    """
    if not os.path.exists(filepath):
        return {}
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}
