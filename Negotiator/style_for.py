def style_for(theme_dict: dict, target_key: str) -> dict:
    # 1. Рекурсивный поиск пути до ключа
    def find_path(d, key):
        for k, v in d.items():
            if k == key:
                return [k]
            if isinstance(v, dict):
                sub = find_path(v, key)
                if sub:
                    return [k] + sub
        return None

    path = find_path(theme_dict, target_key)
    if not path:
        raise KeyError(f"Стиль '{target_key}' не найден в теме")

    # 2. Каскадный сбор: от корня к листу (родительские переопределяются дочерними)
    merged = {}
    current = theme_dict
    for key in path:
        node = current[key]
        if isinstance(node, dict):
            # Собираем только 'плоские' свойства, игнорируя вложенные категории
            merged.update({k: v for k, v in node.items() if not isinstance(v, dict)})
        current = node

    return merged
