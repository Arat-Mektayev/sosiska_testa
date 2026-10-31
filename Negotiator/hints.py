"""
Модуль системы подсказок для симулятора переговоров.
Помогает студентам в обучении принципам HNP.
"""

import random
from typing import List, Dict, Optional
from agent import Agent

class HintSystem:
    """Система подсказок для переговоров"""
    
    def __init__(self, difficulty: str = "medium"):
        """
        Инициализация системы подсказок.
        
        :param difficulty: уровень сложности (easy, medium, hard)
        """
        self.difficulty = difficulty
        self.hints_given = 0
        self.max_hints = self._get_max_hints()
        
        # Базовые подсказки по HNP-принципам
        self.base_hints = [
            "🔍 Попробуйте выяснить, что действительно важно для другой стороны.",
            "💡 Не спорьте о позициях - ищите интересы.",
            "🤝 Ищите взаимовыгодные решения: что вы можете дать, а что получить?",
            "⚖️ Используйте объективные критерии для обоснования своих предложений.",
            "⏳ Учитывайте временные ограничения обеих сторон.",
            "🔄 Рассмотрите возможность обмена: уступить по одному параметру в обмен на другой."
        ]
        
        # Специфические подсказки по параметрам
        self.parameter_hints = {
            "price": [
                "💰 Цена важна, но не всегда является решающим фактором.",
                "📉 Иногда снижение цены можно компенсировать другими условиями.",
                "📈 Повышение цены может быть оправдано лучшим качеством или сроками."
            ],
            "deadline": [
                "⏱️ Срочность может быть рычагом переговоров.",
                "📅 Узнайте, действительно ли срок критичен для другой стороны.",
                "📆 Гибкость по срокам может дать пространство для других уступок."
            ],
            "quality": [
                "⭐ Качество - важный параметр, особенно для повторных сделок.",
                "🌟 Высокое качество может оправдать более высокую цену.",
                "🛠️ Рассмотрите возможность компромисса по качеству в не критичных аспектах."
            ]
        }
    
    def _get_max_hints(self) -> int:
        """Определяет максимальное количество подсказок в зависимости от сложности"""
        if self.difficulty == "easy":
            return 5
        elif self.difficulty == "medium":
            return 3
        else:  # hard
            return 2
    
    def can_give_hint(self) -> bool:
        """Проверяет, можно ли дать ещё подсказку"""
        return self.hints_given < self.max_hints
    
    def get_general_hint(self) -> str:
        """Возвращает общую подсказку по HNP"""
        if not self.can_give_hint():
            return "💡 Вы исчерпали лимит подсказок. Попробуйте применить принципы самостоятельно."
        
        hint = random.choice(self.base_hints)
        self.hints_given += 1
        return f"💡 Подсказка {self.hints_given}/{self.max_hints}: {hint}"
    
    def get_parameter_hint(self, parameter: str) -> str:
        """Возвращает подсказку по конкретному параметру"""
        if not self.can_give_hint():
            return "💡 Вы исчерпали лимит подсказок."
        
        hints = self.parameter_hints.get(parameter, ["🔍 Подумайте о том, как этот параметр влияет на обе стороны."])
        hint = random.choice(hints)
        self.hints_given += 1
        return f"💡 Подсказка {self.hints_given}/{self.max_hints}: {hint}"
    
    def get_contextual_hint(self, situation: str, offer: Dict = None) -> str:
        """
        Возвращает контекстуальную подсказку.
        
        :param situation: тип ситуации ("stuck", "good_progress", "conflict", etc.)
        :param offer: текущее предложение (опционально)
        """
        if not self.can_give_hint():
            return "💡 Вы исчерпали лимит подсказок."
        
        contextual_hints = {
            "stuck": [
                "🔄 Когда переговоры заходят в тупик, попробуйте изменить подход.",
                "🧭 Рассмотрите альтернативные параметры для обсуждения.",
                "🤝 Предложите временный компромисс для разблокировки ситуации."
            ],
            "good_progress": [
                "📈 Вы на правильном пути! Продолжайте искать взаимовыгодные решения.",
                "🎯 Хорошее предложение должно учитывать интересы обеих сторон.",
                "✨ Рассмотрите возможность добавления бонусов для укрепления соглашения."
            ],
            "conflict": [
                "⚖️ Не позволяйте эмоциям мешать поиску решения.",
                "⚖️ Возвращайтесь к объективным критериям.",
                "🤝 Сосредоточьтесь на интересах, а не на позициях."
            ]
        }
        
        hints = contextual_hints.get(situation, self.base_hints)
        hint = random.choice(hints)
        self.hints_given += 1
        return f"💡 Подсказка {self.hints_given}/{self.max_hints}: {hint}"
    
    def get_batna_hint(self, agent: Agent) -> str:
        """Возвращает подсказку, связанную с BATNA"""
        if not self.can_give_hint():
            return "💡 Вы исчерпали лимит подсказок."
        
        batna_hint = f"📊 Помните, что BATNA {agent.name} - это {agent.batna}. Это ваш ориентир."
        self.hints_given += 1
        return f"💡 Подсказка {self.hints_given}/{self.max_hints}: {batna_hint}"
    
    def get_zopa_hint(self, agent_a: Agent, agent_b: Agent) -> str:
        """Возвращает подсказку о ZOPA"""
        if not self.can_give_hint():
            return "💡 Вы исчерпали лимит подсказок."
        
        # Простой анализ ZOPA по цене
        if agent_a.role == "seller":
            seller, buyer = agent_a, agent_b
        else:
            seller, buyer = agent_b, agent_a
        
        seller_min = seller.batna.get("price", 0)
        buyer_max = buyer.batna.get("price", float('inf'))
        
        if seller_min <= buyer_max:
            zopa_hint = f"✅ ZOPA существует: цена от {seller_min:,} до {buyer_max:,} руб."
        else:
            zopa_hint = f"❌ ZOPA отсутствует по цене: минимальная цена продавца ({seller_min:,}) выше максимальной цены покупателя ({buyer_max:,})"
        
        self.hints_given += 1
        return f"💡 Подсказка {self.hints_given}/{self.max_hints}: {zopa_hint}"
    
    def reset_hints(self):
        """Сбрасывает счётчик подсказок"""
        self.hints_given = 0


# Пример использования
if __name__ == "__main__":
    # Тестирование системы подсказок
    hint_system = HintSystem(difficulty="medium")
    
    print("=== ТЕСТИРОВАНИЕ СИСТЕМЫ ПОДСКАЗОК ===")
    
    for i in range(5):
        print(f"\n{i+1}. {hint_system.get_general_hint()}")
    
    print(f"\nМожно ли дать ещё подсказку? {hint_system.can_give_hint()}")