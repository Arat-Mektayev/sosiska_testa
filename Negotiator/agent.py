from math import log2 as log
from localize import localize, format_dict
"""
Модуль агента для симуляции переговоров на основе принципов HNP.
Содержит класс Agent с поддержкой многопараметрической полезности.
"""


class Agent:
    def __init__(self, name, role, batna, weights, reservation=None):
        """
        Инициализация агента переговоров.

        :param name: имя агента (str)
        :param role: роль - "buyer" или "seller"
        :param batna: словарь BATNA значений, например: {"price": 90000, "deadline": 15}
        :param weights: словарь весов параметров, например: {"price": 0.4, "deadline": 0.6}
        :param reservation: опциональная резервная цена (для упрощённой проверки)
        """
        self.name = name
        self.role = role
        self.batna = batna
        self.weights = weights
        self.reservation = reservation

        # Вычисляем минимальную полезность (BATNA-level utility)
        self.min_utility = self.calculate_utility(batna)

    def get_role_coeff(self):
        """
        Возвращает ролевой коэффициент:
        1 для продавца и -1 для покупателя.

        :return: float
        """
        return 1.0 if self.role == "seller" else -1.0

    def get_coeff_for_param(self, param):
        """
        Возвращает коэффициент полезности параметра:
        если для продавца больше - лучше, то возвращает 1;
        если для продавца больше - хуже, то возвращает -1.

        :param param: параметр сделки
        :return: float
        """
        if param == "price" or param == "deadline":
            return 1.0
        if param == "quality" or param == "warranty":
            return -1.0
        # Пусть по умолчанию будет 1
        return 1.0

    def calculate_utility(self, offer) -> float:
        """
        Вычисляет полезность на основе отклонения от BATNA с учётом роли.
        """
        total_utility = 0.0

        # Ролевой коэффициент, влияющий на восприятие параметров переговоров
        role_coeff = self.get_role_coeff()

        for param, weight in self.weights.items():
            coeff = role_coeff * self.get_coeff_for_param(param)
            current_value = offer[param]
            batna_value = self.batna.get(param)

            if batna_value is None:
                continue

            # Определяем, как изменение параметра влияет на агента
            # Используем ratio, но с порогами, чтобы избежать бесконечности
            ratio = current_value / batna_value
            # Применяем log для убывающей полезности
            normalized_value = coeff * log(ratio) if ratio > 0 else 0

            # Умножаем на вес
            total_utility += weight * normalized_value

        return total_utility

    def is_acceptable(self, offer):
        """
        Проверяет, принимает ли агент предложение.

        :param offer: словарь с параметрами предложения
        :return: bool
        """
        utility = self.calculate_utility(offer)
        return utility >= self.min_utility

    def evaluate_offer(self, offer):
        """
        Оценивает, насколько предложение лучше/хуже BATNA.

        :param offer: словарь с параметрами предложения
        :return: разница в полезности (float)
        """
        return self.calculate_utility(offer) - self.min_utility

    def get_batna_utility(self):
        """
        Возвращает минимальную полезность (уровень BATNA).

        :return: float
        """
        return self.min_utility

    def describe_preferences(self):
        """
        Возвращает описание предпочтений агента для отладки/обучения.

        :return: str
        """
        desc = f"Агент {self.name} ({localize(self.role)}):\n"
        desc += f"  BATNA:\n"
        desc = format_dict(self.batna, 2, desc)
        desc += f"  Веса:\n"
        desc = format_dict(self.weights, 2, desc)
        desc += f"  Мин. полезность: {self.min_utility:.3f}\n"
        return desc


    # Пример использования (для тестирования)
if __name__ == "__main__":
    # Создаём агентов
    seller_batna = {"price": 75000, "deadline": 20, "quality": 3}
    seller_weights = {"price": 0.7, "deadline": 0.2, "quality": 0.1}

    buyer_batna = {"price": 90000, "deadline": 15, "quality": 4}
    buyer_weights = {"price": 0.4, "deadline": 0.5, "quality": 0.1}

    seller = Agent("Анна", "seller", seller_batna, seller_weights)
    buyer = Agent("Сергей", "buyer", buyer_batna, buyer_weights)

    # Тестовое предложение
    offer = {"price": 80000, "deadline": 14, "quality": 4}

    print("=== АГЕНТЫ ===")
    print(seller.describe_preferences())
    print(buyer.describe_preferences())

    print("=== ПРЕДЛОЖЕНИЕ ===")
    print(f"Предложение: {offer}")

    print("\n=== ОЦЕНКА ПРОДАВЦА ===")
    seller_utility = seller.calculate_utility(offer)
    seller_diff = seller.evaluate_offer(offer)
    seller_min_utility = seller.get_batna_utility()
    print(f"Полезность: {seller_utility:.3f}")
    print(f"Минимум (BATNA): {seller.get_batna_utility():.3f}")
    print(f"Принимает? {seller_diff >= seller_min_utility}")
    print(f"Разница: {seller_diff:.3f}")

    print("\n=== ОЦЕНКА ПОКУПАТЕЛЯ ===")
    buyer_utility = buyer.calculate_utility(offer)
    buyer_diff = buyer.evaluate_offer(offer)
    buyer_min_utility = buyer.get_batna_utility()
    print(f"Полезность: {buyer_utility:.3f}")
    print(f"Минимум (BATNA): {buyer.get_batna_utility():.3f}")
    print(f"Принимает? {buyer_diff >= buyer_min_utility}")
    print(f"Разница: {buyer_diff:.3f}")