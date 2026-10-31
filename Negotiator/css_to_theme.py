import re
import json
from pathlib import Path

def parse_css_to_json_v2(css_content: str) -> dict:
    result = {
        "basic": {"fonts": {}},
        "Light": {},
        "Dark": {}
    }

    # 1. Парсинг тем
    theme_pattern = r'\[data-theme="(\w+)"\]\s*\{([^}]+)\}'
    themes_found = re.findall(theme_pattern, css_content, re.DOTALL)
    theme_name_map = {"light": "Light", "dark": "Dark"}

    for theme_key, content in themes_found:
        theme_name = theme_name_map.get(theme_key, theme_key.capitalize())
        variables = parse_variables(content)
        result[theme_name] = categorize_and_clean(variables)

    # 2. Парсинг базовых стилей
    content_without_themes = re.sub(theme_pattern, '', css_content, flags=re.DOTALL)
    rule_pattern = r'([^{]+)\{([^}]+)\}'
    global_rules = re.findall(rule_pattern, content_without_themes)
    
    font_stack_str = ""
    
    for selector, props_str in global_rules:
        selector = selector.strip()
        props = parse_properties(props_str)
        
        if selector == "body":
            if 'font-family' in props:
                font_stack_str = props['font-family']
            if 'line-height' in props:
                # Пытаемся превратить в float, если это число
                lh = props['line-height']
                result["basic"]["line_height"] = float(lh) if lh.replace('.','',1).isdigit() else lh
                
        elif selector == "#root":
            result["basic"]["root_layout"] = {
                "width": props.get('width'),
                "height": props.get('height'),
                "overflow": props.get('overflow')
            }
            
        elif selector == "button":
            result["basic"]["button"] = {
                k: v for k, v in props.items() if k in ['cursor', 'border', 'outline']
            }

    # Обработка шрифтов
    if font_stack_str:
        # Разбиваем по запятой, убираем пробелы и кавычки
        fonts = [f.strip().strip("'\"") for f in font_stack_str.split(',')]
        result["basic"]["fonts"]["primary"] = fonts[0] if fonts else "Arial"
        result["basic"]["fonts"]["stack"] = fonts
        result["basic"]["fonts"]["mono"] = "Consolas" # Дефолт для кода, можно добавить в CSS если нужно

    return result

def parse_variables(block_content: str) -> dict:
    variables = {}
    var_pattern = r'--([\w-]+):\s*([^;]+);'
    matches = re.findall(var_pattern, block_content)
    for key, value in matches:
        variables[key] = value.strip()
    return variables

def parse_properties(block_content: str) -> dict:
    props = {}
    prop_pattern = r'([\w-]+):\s*([^;]+);'
    matches = re.findall(prop_pattern, block_content)
    for key, value in matches:
        if not key.startswith('--'):
            props[key] = value.strip()
    return props

def categorize_and_clean(variables: dict) -> dict:
    categorized = {}
    
    # Маппинг префиксов
    prefixes = {
        'bg': 'colors', 'text': 'colors', 'border': 'colors',
        'accent': 'colors', 'error': 'colors', 'success': 'colors',
        'spacing': 'spacing', 'radius': 'radius',
        'font-size': 'typography', 'control': 'controls', 'table': 'controls'
    }
    
    rename_map = {
        'border-color': 'border', 'accent-color': 'accent',
        'error-color': 'error', 'success-color': 'success',
        'control-height': 'height', 'table-row-height': 'table_row_height'
    }

    for key, value in variables.items():
        category = 'misc'
        for prefix, cat_name in prefixes.items():
            if key.startswith(prefix):
                category = cat_name
                break
        
        # Очистка ключа от префикса категории для красоты (опционально)
        # Например spacing-xs -> xs внутри секции spacing
        clean_key = key
        if category == 'spacing' and key.startswith('spacing-'):
            clean_key = key.replace('spacing-', '')
        elif category == 'radius' and key.startswith('radius-'):
            clean_key = key.replace('radius-', '')
        elif category == 'typography' and key.startswith('font-size-'):
            clean_key = key.replace('font-size-', 'size_')
            
        final_key = rename_map.get(clean_key, clean_key.replace('-', '_'))
        
        # Превращаем пиксели в числа там, где это размеры
        if category in ['spacing', 'radius', 'typography', 'controls']:
            if isinstance(value, str) and value.endswith('px'):
                value = int(value.replace('px', ''))
        elif category == 'typography' and clean_key.startswith('size_'):
             if isinstance(value, str) and value.endswith('px'):
                value = int(value.replace('px', ''))

        if category not in categorized:
            categorized[category] = {}
        
        categorized[category][final_key] = value

    return categorized

# --- ЗАПУСК ---
if __name__ == "__main__":
    css_file = Path(".css")
    if css_file.exists():
        css_content = css_file.read_text(encoding="utf-8")
    else:
        # Фоллбэк контент из вашего примера
        css_content = """
        [data-theme="light"] { --bg-primary: #ffffff; --spacing-md: 16px; --font-size-md: 16px; }
        [data-theme="dark"] { --bg-primary: #1a1a1a; --spacing-md: 16px; --font-size-md: 16px; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.5; }
        button { cursor: pointer; border: none; outline: none; }
        #root { width: 100vw; height: 100vh; overflow: hidden; }
        """
    
    result = parse_css_to_json_v2(css_content)
    
    output_file = Path("themes.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Готово! Файл сохранен как {output_file}")
    # print(json.dumps(result, indent=2, ensure_ascii=False))