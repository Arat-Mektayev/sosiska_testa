"""
Модуль с основной логикой переговоров.
Содержит класс NegotiationEngine для управления процессом переговоров.
"""

from typing import Dict, List, Optional, Tuple
from random import random
import math
from localize import format_dict
from functools import wraps

BOUNDS = {
    "price": (1, None),
    "deadline": (1, None),
    "quality": (1, 5),
    "warranty": (1, 10),
}

ROUNDING = {
    "price": 0,      # целое число
    "deadline": 0,
    "quality": 3,    # 3 знака после запятой
    "warranty": 3,
}


def clamp_and_round(bounds: Dict[str, tuple] = None, rounding: Dict[str, int] = None):
    """
    Декоратор, который:
    - ограничивает значения параметров (clamp),
    - округляет их до нужного знака после запятой (round).

    :param bounds: словарь вида {"param": (min_val, max_val)}, None = без границы
    :param rounding: словарь вида {"param": digits}, digits=0 -> целое число
    """
    bounds = bounds or {}
    rounding = rounding or {}

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            if not isinstance(result, dict):
                return result

            processed = result.copy()

            for param in processed:
                val = processed[param]

                # 1. Ограничение (clamp)
                if param in bounds:
                    min_val, max_val = bounds[param]
                    if min_val is not None:
                        val = max(min_val, val)
                    if max_val is not None:
                        val = min(max_val, val)

                # 2. Округление
                if param in rounding:
                    digits = rounding[param]
                    if digits == 0:
                        val = round(val)
                    else:
                        val = round(val, digits)

                processed[param] = val

            return processed

        return wrapper

    return decorator

class NegotiationEngine:
    def __init__(self, agent_a, agent_b, hint_system=None):
        """
        Инициализация движка переговоров.

        :param agent_a: первый агент (Agent)
        :param agent_b: второй агент (Agent)
        :param hint_system: система подсказок (опционально)
        """
        self.agent_a = agent_a
        self.agent_b = agent_b
        self.history = []  # история переговоров
        self.round_count = 0
        self.last_offer = None
        self.hint_system = hint_system

        # В negotiation.py, в классе NegotiationEngine

    def get_agent_utility_analysis(self, offer: Dict) -> Dict:
        """
        Возвращает анализ полезности предложения для обоих агентов.

        :param offer: словарь с параметрами предложения
        :return: словарь с анализом
        """
        utility_a = self.agent_a.calculate_utility(offer)
        utility_b = self.agent_b.calculate_utility(offer)

        return {
            self.agent_a.name: {
                "utility": utility_a,
                "min_utility": self.agent_a.get_batna_utility(),
                "difference": utility_a - self.agent_a.get_batna_utility()
            },
            self.agent_b.name: {
                "utility": utility_b,
                "min_utility": self.agent_b.get_batna_utility(),
                "difference": utility_b - self.agent_b.get_batna_utility()
            }
        }

    def make_counter_offer(self, current_offer: Dict, agent) -> Optional[Dict]:
        """
        Генерирует контрпредложение:
        1. Пытается предложить trade-off.
        2. Если это не работает — предлагает новую структуру (на основе BATNA).
        """

        # Пытаемся сделать trade-off
        counter = self._generate_tradeoff_counter(current_offer, agent)
        if counter and agent.calculate_utility(counter) >= agent.min_utility:
            return counter

        # Если trade-off не сработал — пытаемся предложить новую структуру
        fallback = self._generate_fallback_offer(agent)
        if fallback and agent.calculate_utility(fallback) >= agent.min_utility:
            return fallback

        # Если всё совсем плохо — возвращаем None
        return None

    @clamp_and_round(bounds=BOUNDS, rounding=ROUNDING)
    def _generate_tradeoff_counter(self, offer: Dict, agent) -> Optional[Dict]:
        """
        Ищет параметр, который ухудшает полезность, и улучшает его за счёт другого.
        """
        # Найдём параметр с худшей полезностью
        worst_param = self._find_worst_param(offer, agent)

        if not worst_param:
            return None

        # Найдём параметр, по которому можно уступить
        for param, value in offer.items():
            if param == worst_param:
                continue

            batna_val = agent.batna.get(param)
            if batna_val is None:
                continue

            # Улучшаем worst_param, ухудшая param
            counter = offer.copy()

            # Улучшаем worst_param
            coeff_worst = agent.get_role_coeff() * agent.get_coeff_for_param(worst_param)
            counter[worst_param] *= 1 + 0.05 * coeff_worst

            # Ухудшаем param
            coeff_param = agent.get_role_coeff() * agent.get_coeff_for_param(param)
            counter[param] *= 1 + random() * coeff_param * 0.1

            # Проверим, улучшилась ли полезность
            if agent.calculate_utility(counter) > agent.calculate_utility(offer):
                return counter

        return None

    @clamp_and_round(bounds=BOUNDS, rounding=ROUNDING)
    def _generate_fallback_offer(self, agent) -> Optional[Dict]:
        """
        Генерирует новое предложение, отличное от текущего, но лучше BATNA.
        """
        # Начинаем с BATNA — это база
        fallback = agent.batna.copy()

        # Теперь немного "улучшаем" каждый параметр, чтобы полезность была выше BATNA
        for param, batna_val in fallback.items():
            weight = agent.weights.get(param, 0)
            if weight == 0:
                continue

            coeff = agent.get_role_coeff() * agent.get_coeff_for_param(param)

            # Небольшое улучшение (в пределах разумного)
            fallback[param] *= 1 + coeff * random() * 0.1
        #print("Fallback!")
        # Проверяем, что полезность выше BATNA
        if agent.calculate_utility(fallback) > agent.min_utility:
            return fallback

        return None

    def _find_worst_param(self, offer: Dict, agent) -> Optional[str]:
        """
        Находит параметр с наихудшим вкладом в полезность.
        """
        worst_param = None
        worst_contribution = float('inf')

        for param, weight in agent.weights.items():
            current_val = offer.get(param)
            batna_val = agent.batna.get(param)

            if batna_val is None or current_val is None:
                continue

            coeff = agent.get_role_coeff() * agent.get_coeff_for_param(param)
            ratio = current_val / batna_val
            contribution = coeff * math.log(ratio) if ratio > 0 else 0
            weighted_contribution = weight * contribution

            if weighted_contribution < worst_contribution:
                worst_contribution = weighted_contribution
                worst_param = param

        return worst_param

    def evaluate_negotiation_result(self, final_offer: Optional[Dict]) -> Dict:
        """
        Оценивает результат переговоров.

        :param final_offer: финальное предложение или None
        :return: словарь с оценкой результата
        """
        result = {
            "deal_made": final_offer is not None,
            "final_offer": final_offer,
            "rounds": self.round_count,
        }

        if final_offer:
            analysis = self.get_agent_utility_analysis(final_offer)
            result["utility_analysis"] = analysis

            # Определяем, кто "выиграл" больше
            diff_a = analysis[self.agent_a.name]["difference"]
            diff_b = analysis[self.agent_b.name]["difference"]

            # Используем допуск для определения "равенства"
            if abs(diff_a - diff_b) <= 0.1:  # 10% допуск
                result["advantage"] = "равные условия"
            elif diff_a > diff_b:
                result["advantage"] = self.agent_a.name
            else:
                result["advantage"] = self.agent_b.name

        return result

    def add_to_history(self, actor_name: str, action: str, offer: Dict = None):
        """
        Добавляет запись в историю переговоров.

        :param actor_name: имя участника
        :param action: действие
        :param offer: предложение (опционально)
        """
        self.history.append({
            "round": self.round_count,
            "actor": actor_name,
            "offer": offer.copy() if offer else None
        })

    def generate_result(self, title):
        result = self.evaluate_negotiation_result(
            self.last_offer
        )

        result_text = "🏁 РЕЗУЛЬТАТ ПЕРЕГОВОРОВ\n"
        result_text += f"Сценарий: {title}\n"
        result_text += f"Раундов проведено: {result['rounds']}\n"
        result_text += f"Сделка заключена: {'✅ Да' if result['deal_made'] else '❌ Нет'}\n"
        self.current_results_text = result_text
        if result['deal_made']:
            result_text += f"📝 Финальное соглашение:\n{format_dict(result['final_offer'], 1)}\n"

            analysis = result['utility_analysis']
            result_text += "📊 Анализ полезности:\n"
            for agent_name, data in analysis.items():
                result_text += f"   {agent_name}:\n"
                result_text += f"     Полезность: {data['utility']:.3f}\n"
                result_text += f"     Минимум (BATNA): {data['min_utility']:.3f}\n"
                result_text += f"     Выгода: {data['difference']:.3f}\n"
            if 'advantage' in result:
                result_text += f"\n🏆 Преимущество: {result['advantage']}\n"
        print(result.get('deal_made'))
        # HNP-анализ
        result_text += "🎯 Анализ по принципам HNP:\n"
        if result.get('deal_made'):
            if result.get('advantage') == 'равные условия':
                result_text += "   ✅ Найдено взаимовыгодное решение"
            else:
                result_text += "   ⚠️  Сделка заключена, но одна сторона выиграла больше"
        else:
            if result.get('zopa_exists', False):
                result_text += "   ⚠️  ZOPA существует, но сделка не была достигнута"
            else:
                result_text += "   ❌ ZOPA отсутствует - сделка невозможна"

        return result_text

