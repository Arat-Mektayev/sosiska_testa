import numpy as np
from scipy.optimize import minimize
from scenario import get_builtin_scenarios
from agent import Agent

def pragmatic_analyze_scenario(seller, buyer, items, tolerance=0.1):
    """
    Анализирует сценарий с допуском - ищет 'терпимые' сделки, а не только оптимальные.
    """
    print(f"🔍 Анализ с допуском {tolerance}:")

    # 1. Проверяем BATNA пересечения по каждому параметру
    print("📊 Анализ BATNA по параметрам:")
    conflict_params = []
    for param in items:
        seller_batna = seller.batna.get(param)
        buyer_batna = buyer.batna.get(param)
        seller_coeff = seller.get_role_coeff() * seller.get_coeff_for_param(param)
        buyer_coeff = buyer.get_role_coeff() * buyer.get_coeff_for_param(param)

        if seller_batna is None or buyer_batna is None:
            continue

        if seller_coeff > 0 and buyer_coeff < 0:
            # Продавец хочет больше, покупатель - меньше
            if seller_batna > buyer_batna:
                conflict_params.append((param, f"продавец хочет ≥{seller_batna}, покупатель хочет ≤{buyer_batna}"))
                print(f"   ❌ {param}: КОНФЛИКТ ({seller_batna} > {buyer_batna})")
            else:
                print(f"   ✅ {param}: есть ZOPA [{seller_batna}, {buyer_batna}]")

        elif seller_coeff < 0 and buyer_coeff > 0:
            # Продавец хочет меньше, покупатель - больше
            if seller_batna < buyer_batna:
                conflict_params.append((param, f"продавец хочет ≤{seller_batna}, покупатель хочет ≥{buyer_batna}"))
                print(f"   ❌ {param}: КОНФЛИКТ ({seller_batna} < {buyer_batna})")
            else:
                print(f"   ✅ {param}: есть ZOPA [{buyer_batna}, {seller_batna}]")

    # 2. Ищем "терпимые" сделки с допуском
    print(f"\n🔎 Поиск терпимых сделок (допуск: {tolerance}):")

    # Начинаем с середины BATNA диапазонов
    initial_offer = {}
    for param in items:
        seller_val = seller.batna.get(param, 1)
        buyer_val = buyer.batna.get(param, 1)
        initial_offer[param] = (seller_val + buyer_val) / 2

    # Пробуем разные варианты с небольшими отклонениями
    test_offers = _generate_tolerable_offers(initial_offer, items, seller, buyer, tolerance)

    acceptable_offers = []
    for offer in test_offers:
        u_seller = seller.calculate_utility(offer)
        u_buyer = buyer.calculate_utility(offer)
        batna_seller = seller.get_batna_utility()
        batna_buyer = buyer.get_batna_utility()

        # Проверяем с допуском
        if (u_seller >= batna_seller * (1 - tolerance) and
                u_buyer >= batna_buyer * (1 - tolerance)):
            acceptable_offers.append({
                'offer': offer,
                'utility_seller': u_seller,
                'utility_buyer': u_buyer,
                'score': (u_seller - batna_seller) + (u_buyer - batna_buyer)
            })

    if acceptable_offers:
        # Сортируем по суммарной выгоде
        best_acceptable = max(acceptable_offers, key=lambda x: x['score'])

        print("✅ НАЙДЕНЫ ТЕРПИМЫЕ СДЕЛКИ!")
        print(f"   🤝 Лучшая терпимая сделка:")
        for param, value in best_acceptable['offer'].items():
            if param == "price":
                print(f"      {param}: {value:,.0f} руб.")
            elif param == "deadline":
                print(f"      {param}: {value:.0f} дн.")
            else:
                print(f"      {param}: {value:.1f}")

        print(f"   📈 Полезности:")
        print(f"      {seller.name}: {best_acceptable['utility_seller']:.3f} (BATNA: {seller.get_batna_utility():.3f})")
        print(f"      {buyer.name}: {best_acceptable['utility_buyer']:.3f} (BATNA: {buyer.get_batna_utility():.3f})")
        print(f"   📊 Найдено вариантов: {len(acceptable_offers)}")

        return best_acceptable
    else:
        print("❌ Даже с допуском сделки не найдены")
        return None


def _generate_tolerable_offers(base_offer, items, seller, buyer, tolerance):
    """
    Генерирует варианты предложений вокруг базового с разными отклонениями.
    """
    offers = [base_offer.copy()]

    # Вариации по каждому параметру
    variations = [-0.1, -0.05, 0.05, 0.1, 0.15, 0.2]  # ±10-20%

    for param in items:
        base_value = base_offer[param]
        seller_coeff = seller.get_role_coeff() * seller.get_coeff_for_param(param)
        buyer_coeff = buyer.get_role_coeff() * buyer.get_coeff_for_param(param)

        for variation in variations:
            new_offer = base_offer.copy()

            # Определяем направление улучшения для каждого агента
            if seller_coeff > 0 and buyer_coeff < 0:
                # Противоречивые интересы - пробуем разные балансы
                if abs(variation) < 0.1:  # Близко к середине
                    new_offer[param] = base_value * (1 + variation)
                else:
                    continue

            elif seller_coeff < 0 and buyer_coeff > 0:
                # Противоречивые интересы
                if abs(variation) < 0.1:
                    new_offer[param] = base_value * (1 - variation)
                else:
                    continue

            else:
                # Совпадающие интересы - можно двигаться в одном направлении
                new_offer[param] = base_value * (1 + variation)

            offers.append(new_offer)

    # Добавляем BATNA агентов как крайние варианты
    offers.append(seller.batna.copy())
    offers.append(buyer.batna.copy())

    return offers


def realistic_scenario_assessment(scenario_data):
    """
    Реалистичная оценка сценария с человеческим объяснением.
    """
    seller_data = scenario_data['agents']['agent_a']
    buyer_data = scenario_data['agents']['agent_b']

    seller = Agent(
        name=seller_data['name'],
        role=seller_data['role'],
        batna=seller_data['batna'],
        weights=seller_data['weights']
    )

    buyer = Agent(
        name=buyer_data['name'],
        role=buyer_data['role'],
        batna=buyer_data['batna'],
        weights=buyer_data['weights']
    )

    print(f"\n🎯 СЦЕНАРИЙ: {scenario_data['title']}")
    print("=" * 50)

    # Анализ с разными допусками
    for tolerance in [0.0, 0.05, 0.1, 0.15, 0.2]:
        result = pragmatic_analyze_scenario(seller, buyer, scenario_data['items'], tolerance)
        if result:
            break

    # Человеческая интерпретация
    print(f"\n💡 ПРАКТИЧЕСКАЯ ОЦЕНКА:")

    # Анализ "жесткости" позиций
    seller_rigidity = sum(seller_data['weights'].values()) / len(seller_data['weights'])
    buyer_rigidity = sum(buyer_data['weights'].values()) / len(buyer_data['weights'])

    if seller_rigidity > 0.6 or buyer_rigidity > 0.6:
        print("   ⚠️  Жёсткие позиции - переговоры будут сложными")
    else:
        print("   ✅ Гибкие позиции - есть пространство для манёвра")

    # Анализ совместимости интересов
    common_interests = 0
    for param in scenario_data['items']:
        seller_coeff = seller.get_role_coeff() * seller.get_coeff_for_param(param)
        buyer_coeff = buyer.get_role_coeff() * buyer.get_coeff_for_param(param)

        if seller_coeff * buyer_coeff > 0:  # Одинаковое направление
            common_interests += 1

    if common_interests >= len(scenario_data['items']) / 2:
        print("   ✅ Много общих интересов - проходимость высокая")
    else:
        print("   ⚠️  Противоречивые интересы - нужен торг")

    print("=" * 50)

if __name__ == "__main__":
    # Проанализируем все сценарии
    for name, data in get_builtin_scenarios().items():
        realistic_scenario_assessment(data)

