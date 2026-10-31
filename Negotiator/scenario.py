"""
Модуль для управления сценариями переговоров.
Содержит классы для создания и управления различными сценариями.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from localize import localize
from agent import Agent
import json

@dataclass
class ScenarioConfig:
    """Конфигурация сценария"""
    title: str
    description: str
    items: List[str]  # параметры переговоров: ["price", "deadline", "quality"]
    events: List[Dict] = field(default_factory=list)  # динамические события
    difficulty: str = "medium"  # easy, medium, hard
    agents_data: Dict[str, Dict] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "description": self.description,
            "items": self.items,
            "events": self.events,
            "difficulty": self.difficulty,
            "agents": self.agents_data # Включаем данные агентов
        }

    @staticmethod
    def from_dict(data: Dict) -> 'ScenarioConfig':
        return ScenarioConfig(
            title=data['title'],
            description=data['description'],
            items=data['items'],
            events=data.get('events', []),
            difficulty=data.get('difficulty', 'medium'),
            agents_data=data.get('agents', {}) # Получаем данные агентов
        )

class Scenario:
    """Сценарий переговоров"""

    def __init__(self, config: ScenarioConfig, seller_agent: Agent, buyer_agent: Agent):
        """
        Инициализация сценария.

        :param config: конфигурация сценария
        :param seller_agent: агент-продавец
        :param buyer_agent: агент-покупатель
        """
        self.config = config
        self.seller = seller_agent
        self.buyer = buyer_agent
        self.current_round = 0
        self.events_triggered = []

    def get_initial_offer(self) -> Dict:
        """
        Возвращает начальное предложение (обычно от покупателя).

        :return: словарь с начальным предложением
        """
        # Генерируем разумное начальное предложение
        initial = {}

        for item in self.config.items:
            seller_val = self.seller.batna.get(item, 1)
            buyer_val = self.buyer.batna.get(item, 10)
            initial[item] = (seller_val + buyer_val) / 2

        return initial

    def check_events(self, round_num: int) -> List[Dict]:
        """
        Проверяет, срабатывают ли события в текущем раунде.

        :param round_num: номер текущего раунда
        :return: список сработавших событий
        """
        triggered = []
        for event in self.config.events:
            # Событие срабатывает по раунду
            if event.get("round") == round_num:
                triggered.append(event)
            # Событие срабатывает по условию
            elif "condition" in event:
                # Пока просто пример - можно расширить
                if round_num >= event.get("min_round", 3):
                    triggered.append(event)
        self.events_triggered.extend(triggered)
        return triggered

    def apply_event(self, event: Dict, agent_a: Agent, agent_b: Agent):
        """
        Применяет эффект события к агентам.

        :param event: словарь с описанием события
        :param agent_a: первый агент
        :param agent_b: второй агент
        """
        effect = event.get("effect", "")
        # Примеры эффектов:
        if effect == "urgency_buyer":
            # Покупатель становится более срочным
            if "deadline" in agent_b.batna:
                agent_b.batna["deadline"] = max(5, agent_b.batna["deadline"] - 3)
        elif effect == "pressure_seller":
            # Продавец теряет терпение
            if "price" in agent_a.batna:
                agent_a.batna["price"] = agent_a.batna["price"] * 0.95
        elif effect == "new_info_buyer":
            # Покупатель узнает о конкуренте
            agent_b.weights["price"] = min(0.8, agent_b.weights["price"] + 0.2)
        elif effect == "flexibility_seller":
            # Продавец становится более гибким
            agent_a.weights["deadline"] = min(0.5, agent_a.weights["deadline"] + 0.2)

    def get_scenario_info(self) -> str:
        """
        Возвращает информацию о сценарии для пользователя.

        :return: строка с описанием
        """
        info = f"=== СЦЕНАРИЙ: {self.config.title} ===\n"
        info += f"{self.config.description}\n\n"
        info += f"Параметры переговоров: {', '.join(map(localize, self.config.items))}\n"
        info += f"Уровень сложности: {localize(self.config.difficulty)}\n\n"
        info += "=== УЧАСТНИКИ ===\n"
        info += self.seller.describe_preferences()
        info += "\n"
        info += self.buyer.describe_preferences()

        return info

class ScenarioLoader:
    """Загрузчик сценариев из внешних файлов"""

    @staticmethod
    def load_from_json(filepath: str) -> Optional['Scenario']:
        """
        Загружает сценарий из JSON-файла.

        :param filepath: путь к файлу
        :return: объект Scenario или None
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return create_scenario(data)
        except FileNotFoundError:
            print(f"Файл сценария не найден: {filepath}")
            return None
        except json.JSONDecodeError as e:
            print(f"Ошибка парсинга JSON в файле {filepath}: {e}")
            return None
        except Exception as e:
            print(f"Ошибка загрузки сценария из {filepath}: {e}")
            return None

# Предопределённые сценарии

def get_builtin_scenarios() -> Dict[str, Dict]:
    """
    Возвращает словарь встроенного сценария (имя -> данные).
    Это похоже на ваш старый create_scenario_by_name, но возвращает данные.
    """
    return {
        "Продажа оборудования": {
            "title": "Продажа оборудования",
            "description": "Компания продает подержанное оборудование. Простые переговоры по цене и срокам.",
            "items": ["price", "deadline"],
            "difficulty": "easy",
            "events": [
                {"round": 2, "effect": "urgency_buyer", "description": "Грант закрывается скоро"},
                {"round": 4, "effect": "pressure_seller", "description": "Поставщик нуждается в срочной оплате"}
            ],
            "agents": {
                "agent_a": {
                    "name": "ОборудМастер",
                    "batna": {"price": 50000, "deadline": 10},
                    "role": "seller",
                    "weights": {"price": 0.8, "deadline": 0.2}
                },
                "agent_b": {
                    "name": "МалыйБизнес",
                    "batna": {"price": 70000, "deadline": 15},
                    "role": "buyer",
                    "weights": {"price": 0.7, "deadline": 0.3}
                }
            }
        },
        "Поставка программного обеспечения": {
            "title": "Поставка программного обеспечения",
            "description": "Клиент нуждается в специализированном ПО для автоматизации бизнес-процессов. Есть срочная необходимость до конца квартала.",
            "items": ["price", "deadline", "quality"],
            "difficulty": "medium",
            "events": [
                {"round": 3, "effect": "urgency_buyer", "description": "Клиенту срочно нужно ПО"}
            ],
            "agents": {
                "agent_a": {
                    "name": "TechSoft Ltd",
                    "batna": {"price": 75000, "deadline": 20, "quality": 3},
                    "role": "seller",
                    "weights": {"price": 0.7, "deadline": 0.2, "quality": 0.1}
                },
                "agent_b": {
                    "name": "БизнесГрупп",
                    "batna": {"price": 90000, "deadline": 15, "quality": 4},
                    "role": "buyer",
                    "weights": {"price": 0.4, "deadline": 0.5, "quality": 0.1}
                }
            }
        },
        "Финансирование по гранту": {
            "title": "Финансирование по гранту",
            "description": "Научная лаборатория ищет поставщика оборудования для проекта по гранту. Строгий бюджет и сжатые сроки.",
            "items": ["deadline", "quality", "warranty"],
            "difficulty": "hard",
            "events": [],
            "agents": {
                "agent_a": {
                    "name":"НаучОборуд",
                    "batna":{"deadline": 20, "quality": 3, "warranty": 5},
                    "role": "seller",
                    "weights":{"deadline": 0.6, "quality": 0.3, "warranty": 0.1}
                },
                "agent_b": {
                    "name":"Лаборатория",
                    "batna":{"deadline": 25, "quality": 5, "warranty": 6},
                    "role": "buyer",
                    "weights":{"deadline": 0.3, "quality": 0.4, "warranty": 0.3}
                }
            }
        },
        "Подряд на строительство": {
            "title": "Подряд на строительство",
            "description": "Государственный заказчик ищет подрядчика для строительства административного здания. Важны качество и сроки.",
            "items": ["price", "deadline", "quality", "warranty"],
            "difficulty": "hard",
            "events": [
                {"round": 2, "effect": "new_info_buyer", "description": "Появился новый конкурент"},
                {"round": 4, "effect": "flexibility_seller", "description": "Подрядчик готов ускорить сроки"}
            ],
            "agents": {
                "agent_a": {
                    "name": "СтройПроект",
                    "batna": {"price": 2000000, "deadline": 90, "quality": 3, "warranty": 2},
                    "role": "seller",
                    "weights": {"price": 0.5, "deadline": 0.2, "quality": 0.2, "warranty": 0.1}
                },
                "agent_b": {
                    "name": "Горадминистрация",
                    "batna": {"price": 3000000, "deadline": 60, "quality": 5, "warranty": 3},
                    "role": "buyer",
                    "weights": {"price": 0.3, "deadline": 0.4, "quality": 0.2, "warranty": 0.1}
                }
            }
        },
    }

def list_available_scenarios() -> List[str]:
    """
    Возвращает список доступных сценариев.

    :return: список имён сценариев
    """
    return list(get_builtin_scenarios().keys())


def create_scenario(data: Dict) -> 'Scenario':
    config = ScenarioConfig.from_dict(data)

    # --- Создание агентов из данных JSON ---
    agents_info = config.agents_data

    agent_a_data = agents_info['agent_a']
    agent_b_data = agents_info['agent_b']

    # Создаём объекты Agent
    agent_a = Agent(
        name=agent_a_data['name'],
        role=agent_a_data['role'],
        batna=agent_a_data['batna'],
        weights=agent_a_data['weights']
    )

    agent_b = Agent(
        name=agent_b_data['name'],
        role=agent_b_data['role'],
        batna=agent_b_data['batna'],
        weights=agent_b_data['weights']
    )

    return Scenario(config, agent_a, agent_b)

def load_scenario_by_name(name: str, directory: str = "scenarios/") -> Optional['Scenario']:
    """
    Загружает сценарий по имени.
    Определяет, встроенный это или файловый сценарий.
    """
    builtin_scenarios = get_builtin_scenarios()

    # Проверяем, является ли имя встроенным (с префиксом)
    if name in builtin_scenarios.keys():
        return create_scenario(builtin_scenarios[name]) #ScenarioLoader.load_builtin(name)
    # Иначе ищем файл
    else:
        # Сначала проверим, есть ли файл с таким именем
        filepath = os.path.join(directory, f"{name}.json")
        if os.path.exists(filepath):
            return ScenarioLoader.load_from_json(filepath)
        else:
            print(f"Файл сценария '{filepath}' не найден.")
            return None

# --- Для тестирования ---
if __name__ == "__main__":
    print("=== ДОСТУПНЫЕ СЦЕНАРИИ (встроенные и файловые) ===")
    scenarios = list_available_scenarios()
    for name in scenarios:
        print(f"- {name}")

    print("\n=== ЗАГРУЗКА ВСТРОЕННОГО СЦЕНАРИЯ ===")
    builtin_scenario = load_scenario_by_name("Поставка программного обеспечения")
    if builtin_scenario:
        print(builtin_scenario.get_scenario_info())
        print(f"\nНачальное предложение: {builtin_scenario.get_initial_offer()}")
    else:
        print("Не удалось загрузить встроенный сценарий.")

    print("\n=== ЗАГРУЗКА ФАЙЛОВОГО СЦЕНАРИЯ ===")
    # Попробуем загрузить файл, если он есть
    import os
    if os.path.exists("scenarios/software_deal2.json"): # Пример имени файла
        file_scenario = load_scenario_by_name("software_deal2")
        if file_scenario:
             print(file_scenario.get_scenario_info())
             print(f"\nНачальное предложение: {file_scenario.get_initial_offer()}")
        else:
             print("Не удалось загрузить файловый сценарий.")
    else:
        print("Файловый сценарий 'software_deal2.json' не найден в папке 'scenarios'.")
