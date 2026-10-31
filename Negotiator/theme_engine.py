import json
import customtkinter as ctk
from typing import Optional, Dict, Any, Literal
from pathlib import Path

# Типы вариантов кнопок
WidgetVariant = Literal["primary", "secondary", "tertiary", "error", "success", "ghost"]

class ThemeEngine:
    def __init__(self, json_path: str = "themes.json"):
        self.data = self._load_theme(json_path)
        self.basic = self.data.get("basic", {})
        self.current_theme_data = {}

    def _load_theme(self, path: str) -> dict:
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"Файл темы не найден: {path}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def set_theme(self, mode: Literal["Light", "Dark"]):
        """Переключает активную тему (Light или Dark)."""
        if mode not in self.data:
            raise ValueError(f"Тема '{mode}' не найдена. Доступны: {list(self.data.keys())}")
        self.current_theme_data = self.data[mode]
        # Применяем глобальную тему CTk для системных элементов
        ctk.set_appearance_mode(mode.lower())

    def _parse_val(self, val: Any) -> Any:
        """Конвертирует '32px' в 32, оставляет остальное как есть."""
        if isinstance(val, str) and val.endswith("px"):
            return int(val[:-2])
        return val
    
    def _get_font(self, size_key: str = "size_md") -> ctk.CTkFont:
        """Создает объект шрифта на основе basic + typography."""
        font_family = self.basic.get("fonts", {}).get("primary", "Arial")
        size_val = self.basic.get("typography", {}).get(size_key, 16)
        
        # На случай если размер вдруг остался строкой
        size_val = self._parse_val(size_val)
        print(font_family, size_val, size_key)
        return ctk.CTkFont(family=font_family, size=size_val)

    def get_widget_style(
        self, 
        widget_type: Literal["button", "entry", "frame", "label"], 
        variant: WidgetVariant = "primary",
        size: Literal["xs", "sm", "md", "lg", "xl"] = "md"
    ) -> Dict[str, Any]:
        """
        Генерирует словарь стилей для виджета.
        
        Args:
            widget_type: Тип виджета ('button', 'entry', etc.)
            variant: Стиль варианта ('primary', 'error', etc.)
            size: Размер шрифта и отступов ('sm', 'md', etc.)
        """
        colors = self.current_theme_data.get("colors", {})
        radius = self.current_theme_data.get("radius", {})
        controls = self.current_theme_data.get("controls", {})
        
        # Базовые параметры из basic
        base_radius = self._parse_val(radius.get("md", "6px")) # Дефолтный радиус
        height = self._parse_val(controls.get("height", "32px"))
        font = self._get_font(f"size_{size}")

        style = {
            "font": font,
            "corner_radius": base_radius,
        } if widget_type in ("button", "label") else {}

        # --- Логика для КНОПОК ---
        if widget_type == "button":
            # Определение цветов пары (bg, hover, text)
            if variant == "primary":
                fg = colors.get("accent")
                hover = colors.get("accent_hover")
                text = "#FFFFFF" # Белый текст на акценте
            elif variant == "secondary":
                fg = colors.get("bg_secondary")
                hover = colors.get("bg_tertiary")
                text = colors.get("text_primary")
            elif variant == "tertiary":
                fg = "transparent"
                hover = colors.get("bg_secondary")
                text = colors.get("text_primary")
            elif variant == "error":
                fg = colors.get("error")
                hover = "#c82333" # Чуть темнее ошибки
                text = "#FFFFFF"
            elif variant == "success":
                fg = colors.get("success")
                hover = "#218838"
                text = "#FFFFFF"
            elif variant == "ghost":
                fg = "transparent"
                hover = "transparent"
                text = colors.get("accent")
            else:
                fg = colors.get("bg_primary")
                hover = colors.get("bg_secondary")
                text = colors.get("text_primary")

            style.update({
                "fg_color": fg,
                "hover_color": hover,
                "text_color": text,
                "height": height,
            })
            
            # Для tertiary/ghost убираем рамку или делаем её мягкой
            if variant in ["tertiary", "ghost"]:
                style["border_width"] = 0
            else:
                style["border_width"] = 0 # В CSS было border: none, но можно добавить 1 для контура

        # --- Логика для ПОЛЕЙ ВВОДА (Entry) ---
        elif widget_type == "entry":
            style.update({
                "fg_color": colors.get(f"bg_{variant}"),
                "border_color": colors.get("border"),
                "text_color": colors.get("text_primary"),
                #"placeholder_text_color": colors.get("text_tertiary"),
                #"height": height,
                "corner_radius": base_radius,
                "border_width": 1,
            })

        # --- Логика для РАМОК (Frame) ---
        elif widget_type == "frame":
            bg_map = {
                "primary": colors.get("bg_primary"),
                "secondary": colors.get("bg_secondary"),
                "tertiary": colors.get("bg_tertiary"),
                "error": colors.get("error_bg"),
                "success": colors.get("success"), # Или отдельный цвет фона успеха
            }
            style.update({
                "fg_color": bg_map.get(variant, colors.get("bg_primary")),
                "corner_radius": base_radius,
                "border_width": 0,
                "border_color": colors.get("border"),
            })
            
        # --- Логика для ТЕКСТА (Label) ---
        elif widget_type == "label":
            text_map = {
                "primary": colors.get("text_primary"),
                "secondary": colors.get("text_secondary"),
                "tertiary": colors.get("text_tertiary"),
                "error": colors.get("error"),
                "success": colors.get("success"),
                "accent": colors.get("accent"),
            }
            style.update({
                "text_color": text_map.get(variant, colors.get("text_primary")),
                "corner_radius": 0,
            })
            # Убираем высоту для лейбла, она ему не нужна так же как кнопке
            style.pop("height", None)

        return style

# --- Глобальный экземпляр для удобства ---
theme = ThemeEngine()

# Хелперы для быстрого доступа
def get_label_style(variant: WidgetVariant = "primary", size: str = "md"):
    return theme.get_widget_style("label", variant, size)

def get_button_style(variant: WidgetVariant = "primary", size: str = "md"):
    return theme.get_widget_style("button", variant, size)

def get_entry_style(size: str = "md"):
    return theme.get_widget_style("entry", "primary", size)

def get_frame_style(variant: WidgetVariant = "primary"):
    return theme.get_widget_style("frame", variant, "md")