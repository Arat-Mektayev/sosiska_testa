import numpy as np
import matplotlib.pyplot as plt

# ========================================
# 1. ЕДИНЫЙ КОНФИГУРАЦИОННЫЙ БЛОК
# Все параметры — здесь. Меняешь — всё перестраивается.
# ========================================

cfg = {
    # Диапазоны для графика
    "price_range": (70_000, 100_000),
    "deadline_range": (10, 25),

    # BATNA (альтернативы)
    "seller_batna": {"price": 75_000, "deadline": 20},
    "buyer_batna":  {"price": 90_910, "deadline": 15},

    # Веса в функции полезности (0.0 — 1.0, сумма = 1.0)
    "seller_weights": {"price": 0.7, "deadline": 0.3},  # Чем позже — тем лучше
    "buyer_weights":  {"price": 0.4, "deadline": 0.6},  # Чем раньше — тем лучше
}

# ========================================
# 2. ФУНКЦИИ ПОЛЕЗНОСТИ (UTILITY)
# ========================================

def utility_seller(price, deadline, cfg):
    # Продавец: чем выше цена и позже срок — тем лучше
    norm_price = price / cfg["price_range"][1]
    # Срок: чем позже (ближе к max_deadline) — тем лучше
    norm_deadline = (deadline - cfg["deadline_range"][0]) / (cfg["deadline_range"][1] - cfg["deadline_range"][0])
    return (cfg["seller_weights"]["price"] * norm_price +
            cfg["seller_weights"]["deadline"] * norm_deadline)

def utility_buyer(price, deadline, cfg):
    # Покупатель: чем ниже цена и раньше срок — тем лучше
    norm_price = (cfg["price_range"][1] - price) / (cfg["price_range"][1] - cfg["price_range"][0])
    # Срок: чем раньше (меньше deadline) — тем лучше
    norm_deadline = (cfg["deadline_range"][1] - deadline) / (cfg["deadline_range"][1] - cfg["deadline_range"][0])
    return (cfg["buyer_weights"]["price"] * norm_price +
            cfg["buyer_weights"]["deadline"] * norm_deadline)

# ========================================
# 3. АВТОМАТИЧЕСКИЙ РАСЧЁТ MIN UTILITY (из BATNA)
# ========================================

seller_min_u = utility_seller(
    cfg["seller_batna"]["price"],
    cfg["seller_batna"]["deadline"],
    cfg
)

buyer_min_u = utility_buyer(
    cfg["buyer_batna"]["price"],
    cfg["buyer_batna"]["deadline"],
    cfg
)

print(f"Мин. полезность продавца (из BATNA): {seller_min_u:.3f}")
print(f"Мин. полезность покупателя (из BATNA): {buyer_min_u:.3f}")

# ========================================
# 4. ПОСТРОЕНИЕ ZOPA
# ========================================

prices = np.linspace(cfg["price_range"][0], cfg["price_range"][1], 100)
deadlines = np.linspace(cfg["deadline_range"][0], cfg["deadline_range"][1], 100)
Price, Deadline = np.meshgrid(prices, deadlines)
ZOPA = np.zeros_like(Price)

for i in range(deadlines.size):
    for j in range(prices.size):
        p = Price[i, j]
        d = Deadline[i, j]
        u_s = utility_seller(p, d, cfg)
        u_b = utility_buyer(p, d, cfg)
        if u_s >= seller_min_u and u_b >= buyer_min_u:
            ZOPA[i, j] = 1

# ========================================
# 5. ВИЗУАЛИЗАЦИЯ
# ========================================

plt.figure(figsize=(10, 6))
plt.contourf(Price / 1000, Deadline, ZOPA, levels=[0, 0.5, 1], colors=['red', 'green'], alpha=0.5)
plt.colorbar(ticks=[0, 1], label='В ZOPA', boundaries=[-0.5, 0.5, 1.5])

plt.xlabel("Цена (тыс. руб.)")
plt.ylabel("Срок поставки (дней)")
plt.title("ZOPA: зона возможного соглашения\n(настраиваемая система)")

# BATNA-точки
plt.scatter(
    cfg["seller_batna"]["price"] / 1000,
    cfg["seller_batna"]["deadline"],
    color='blue', s=120, label="BATNA продавца", edgecolor='black', zorder=5
)
plt.scatter(
    cfg["buyer_batna"]["price"] / 1000,
    cfg["buyer_batna"]["deadline"],
    color='purple', s=120, label="BATNA покупателя", edgecolor='black', zorder=5
)

plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()