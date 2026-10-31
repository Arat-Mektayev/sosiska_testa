#!/usr/bin/env python3
"""
Графический интерфейс для HNP Negotiation Simulator
Использует CustomTkinter + ThemeEngine для современного внешнего вида
"""
import customtkinter as ctk
from tkinter import messagebox, filedialog

from scenario import load_scenario_by_name, list_available_scenarios, ScenarioLoader
from negotiation import NegotiationEngine, ROUNDING
from hints import HintSystem
from localize import localize, format_dict
from theme_engine import theme, get_button_style, get_entry_style, get_frame_style, get_label_style
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

# === Инициализация темы ===
# Доступные темы: "Light", "Dark" (должны совпадать с ключами в themes.json)
theme.set_theme("Light")

sizes = {
    "main_frame_buttons": {
        "width": 200,
        "height": 40
    },
    "action_panel_buttons": {
        "width": 220,
        "height": 35
    },
    "return_buttons": {
        "width": 100,
        "height": 30
    },
}

class NegotiationGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Настройки окна
        self.title("🎓 HNP Negotiation Simulator")
        self.geometry("1000x700")
        self.minsize(800, 600)

        # Применяем цвет фона окна из темы
        self.configure(fg_color=theme.current_theme_data["colors"]["bg_primary"])

        # Переменные состояния
        self.current_scenario = None
        self.negotiation_engine = None
        self.last_user_offer = None
        self.is_negotiation_active = False
        self.current_view = "main"  # "main", "negotiation", "results"

        # Создание интерфейса
        self.create_widgets()
        self.update_scenario_list()

    def create_widgets(self):
        """Создание всех виджетов интерфейса"""
        # Основной контейнер
        self.main_container = ctk.CTkFrame(self, **get_frame_style("secondary"))
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Кнопка возврата (изначально скрыта)
        self.back_button = ctk.CTkButton(
            self,
            text="↩️ На главное окно",
            command=self.return_to_main,
            **get_button_style('secondary', 'sm')
        )

        # Создаем фреймы для разных представлений
        self.main_frame = ctk.CTkFrame(self.main_container, **get_frame_style("primary"))
        self.negotiation_frame = ctk.CTkFrame(self.main_container, **get_frame_style("primary"))
        self.results_frame = ctk.CTkFrame(self.main_container, **get_frame_style("secondary"))

        # Настройка представлений
        self.setup_main_view()
        self.setup_negotiation_view()
        self.setup_results_view()

        # Показываем главное представление
        self.show_view("main")

    def show_view(self, view_name: str):
        """Показ определенного представления"""
        self.current_view = view_name

        # Скрываем все фреймы
        self.main_frame.pack_forget()
        self.negotiation_frame.pack_forget()
        self.results_frame.pack_forget()

        # Показываем нужный фрейм
        if view_name == "main":
            self.main_frame.pack(fill="both", expand=True)
            self.back_button.pack_forget()
        elif view_name == "negotiation":
            self.negotiation_frame.pack(fill="both", expand=True)
            self.back_button.pack(side="bottom", anchor="se", padx=20, pady=10)
        elif view_name == "results":
            self.results_frame.pack(fill="both", expand=True)
            self.back_button.pack(side="bottom", anchor="se", padx=20, pady=10)

    def return_to_main(self):
        """Возврат к главной странице"""
        if self.current_view == "negotiation":
            if self.is_negotiation_active:
                result = messagebox.askyesno(
                    "Подтверждение",
                    "Переговоры еще не завершены. Вы уверены, что хотите выйти?"
                )
                if not result:
                    return

        self.show_view("main")

    def start_negotiation(self):
        """Начало переговоров"""
        if not self.current_scenario:
            messagebox.showerror("Ошибка", "Пожалуйста, выберите сценарий")
            return

        self.negotiation_engine = NegotiationEngine(
            self.current_scenario.seller,
            self.current_scenario.buyer
        )
        self.negotiation_engine.hint_system = HintSystem(difficulty=self.current_scenario.config.difficulty)

        self.last_user_offer = None
        self.negotiation_engine.last_offer = self.current_scenario.get_initial_offer()
        self.negotiation_engine.round_count = 1
        self.is_negotiation_active = True

        self.update_negotiation_interface()
        self.show_view("negotiation")
        self.show_agent_response("Система", "🎯 Начальное предложение сгенерировано")

    # --- Настройка представлений ---

    def setup_main_view(self):
        """Настройка главного представления"""
        # Заголовок
        title_label = ctk.CTkLabel(
            self.main_frame,
            text="🎓 HNP Negotiation Simulator",
            **get_label_style('primary', 'xl') # Используем стиль для крупного текста
        )
        # Убираем лишние параметры кнопки у лейбла
        title_label
        title_label.pack(pady=20)

        # Описание
        desc_text = (
            "Обучающий симулятор переговоров на основе принципов\n Harvard Negotiation Project."
        )
        desc_label = ctk.CTkLabel(
            self.main_frame,
            text=desc_text,
            **get_label_style('secondary', 'md'),
            wraplength=800,
            justify="center"
        )
        desc_label
        desc_label.pack(pady=10)

        # Фрейм для выбора сценария
        scenario_frame = ctk.CTkFrame(self.main_frame, **get_frame_style("secondary"))
        scenario_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(
            scenario_frame,
            text="Выберите сценарий:",
            **get_label_style('primary', 'lg')
        )

        # Список сценариев
        self.scenario_listbox = ctk.CTkComboBox(
            scenario_frame,
            values=[],
            width=600,
            **get_entry_style('md')
        )
        self.scenario_listbox.pack(pady=10)

        # Кнопки
        button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        button_frame.pack(pady=20)

        self.start_button = ctk.CTkButton(
            button_frame,
            **get_button_style('primary', 'md'),
            text="🚀 Начать переговоры",
            command=self.start_negotiation,
        )
        self.start_button.pack(side="left", padx=10)

        load_button = ctk.CTkButton(
            button_frame,
            **get_button_style('secondary', 'md'),
            text="📂 Загрузить из файла",
            command=self.load_scenario_from_file,
        )
        load_button.pack(side="left", padx=10)

        # Информация о выбранном сценарии
        self.scenario_info_frame = ctk.CTkFrame(self.main_frame, **get_frame_style("primary"))
        self.scenario_info_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.scenario_info_text = ctk.CTkTextbox(
            self.scenario_info_frame,
            wrap="word",
            width=600,
            height=200,
            **get_entry_style('md')
        )
        self.scenario_info_text.pack(fill="both", expand=True, padx=10, pady=10)
        self.scenario_info_text.configure(state="disabled")

        self.scenario_listbox.configure(command=self.on_scenario_selected)

    def setup_negotiation_view(self):
        """Настройка представления переговоров"""
        main_paned_window = ctk.CTkFrame(self.negotiation_frame, fg_color="transparent")
        main_paned_window.pack(fill="both", expand=True, padx=20, pady=20)

        # --- Левая панель: Действия ---
        action_panel = ctk.CTkFrame(main_paned_window, **get_frame_style("secondary"), width=250)
        action_panel.pack(side="left", fill="y", padx=(0, 10))
        action_panel.pack_propagate(False)

        ctk.CTkLabel(
            action_panel,
            text="Действия:",
            **get_label_style('primary', 'lg')
        ).pack(pady=(10, 5), padx=10, anchor="w")

        # Кнопки действий
        self.make_offer_button = ctk.CTkButton(
            action_panel,
            **get_button_style('primary', 'sm'),
            text="📝 Предложить условия",
            command=self.make_offer_dialog,
        )
        self.make_offer_button.pack(pady=5, padx=10, fill="x")

        self.ask_question_button = ctk.CTkButton(
            action_panel,
            **get_button_style('primary', 'sm'),
            text="❓ Задать вопрос",
            command=self.ask_question_dialog,
        )
        self.ask_question_button.pack(pady=5, padx=10, fill="x")

        self.get_hint_button = ctk.CTkButton(
            action_panel,
            **get_button_style('primary', 'sm'),
            text="💡 Получить подсказку",
            command=self.get_hint,
        )
        self.get_hint_button.pack(pady=5, padx=10, fill="x")

        self.accept_button = ctk.CTkButton(
            action_panel,
            **get_button_style('success', 'sm'),
            text="✅ Принять предложение",
            command=self.accept_offer,
        )
        self.accept_button.pack(pady=5, padx=10, fill="x")

        self.end_button = ctk.CTkButton(
            action_panel,
            **get_button_style('error', 'sm'),
            text="⏹️ Завершить переговоры",
            command=self.end_negotiation,
        )
        self.end_button.pack(pady=(5, 10), padx=10, fill="x")

        # --- Правая панель: Информация ---
        info_panel = ctk.CTkFrame(main_paned_window, **get_frame_style("primary"))
        info_panel.pack(side="right", fill="both", expand=True)

        self.round_label = ctk.CTkLabel(
            info_panel,
            text="Раунд 1",
            **get_label_style('primary', 'lg')
        )
        self.round_label
        self.round_label.pack(pady=5)

        offers_frame = ctk.CTkFrame(info_panel, fg_color="transparent")
        offers_frame.pack(fill="x", padx=10, pady=5)

        user_offer_frame = ctk.CTkFrame(offers_frame, **get_frame_style("secondary"))
        user_offer_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        ctk.CTkLabel(
            user_offer_frame,
            text="📝 Наше предложение:",
            **get_label_style('primary', 'sm')
        ).pack(anchor="w", padx=5, pady=2)

        self.user_offer_textbox = ctk.CTkTextbox(
            user_offer_frame,
            height=95,
            wrap="word",
            **get_entry_style('md')
        )
        self.user_offer_textbox.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        self.user_offer_textbox.configure(state="disabled")

        agent_offer_frame = ctk.CTkFrame(offers_frame, **get_frame_style("secondary"))
        agent_offer_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))

        ctk.CTkLabel(
            agent_offer_frame,
            text="🤖 Предложение агента:",
            **get_label_style('primary', 'sm')
        ).pack(anchor="w", padx=5, pady=2)

        self.agent_offer_textbox = ctk.CTkTextbox(
            agent_offer_frame,
            height=80,
            wrap="word",
            **get_entry_style('md')
        )
        self.agent_offer_textbox.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        self.agent_offer_textbox.configure(state="disabled")

        hints_frame = ctk.CTkFrame(info_panel, **get_frame_style("secondary"))
        hints_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            hints_frame,
            text="💡 Подсказки:",
            **get_label_style('primary', 'sm')
        ).pack(anchor="w", padx=5, pady=2)

        self.hints_textbox = ctk.CTkTextbox(
            hints_frame,
            height=60,
            wrap="word",
            **get_entry_style('sm')
        )
        self.hints_textbox.pack(fill="x", padx=5, pady=(0, 5))
        self.hints_textbox.configure(state="disabled")

        response_frame = ctk.CTkFrame(info_panel, **get_frame_style("secondary"))
        response_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            response_frame,
            text="💬 Ответ агента:",
            **get_label_style('primary', 'sm')
        ).pack(anchor="w", padx=5, pady=2)

        self.response_textbox = ctk.CTkTextbox(
            response_frame,
            wrap="word",
            **get_entry_style('md')
        )
        self.response_textbox.pack(fill="x", padx=5, pady=(0, 5))
        self.response_textbox.configure(state="disabled")

    def setup_results_view(self):
        """Настройка представления результатов"""
        self.result_title_label = ctk.CTkLabel(
            self.results_frame,
            text="🏁 Результаты переговоров",
            **get_label_style('primary', 'xl')
        )
        self.result_title_label
        self.result_title_label.pack(pady=20)

        self.results_textbox = ctk.CTkTextbox(
            self.results_frame,
            wrap="word",
            width=700,
            height=400,
            **get_entry_style('md')
        )
        self.results_textbox.pack(fill="both", expand=True, padx=20, pady=10)
        self.results_textbox.configure(state="disabled")

        button_frame = ctk.CTkFrame(self.results_frame, fg_color="transparent")
        button_frame.pack(pady=20)

        save_report_button = ctk.CTkButton(
            button_frame,
            **get_button_style('primary', 'md'),
            text="📄 Сохранить отчёт",
            command=self.save_negotiation_report,
        )
        save_report_button.pack(side="left", padx=10)

    def save_negotiation_report(self):
        """Сохраняет отчёт о результатах переговоров в файл .docx."""
        if not hasattr(self, 'current_results_text'):
             messagebox.showwarning("Предупреждение", "Нет данных для сохранения. Пожалуйста, завершите переговоры.")
             return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".docx",
            filetypes=[("Word files", "*.docx"), ("All files", "*.*")],
            title="Сохранить отчёт о переговорах"
        )

        if not file_path:
            return

        try:
            doc = Document()
            title = doc.add_heading('Результаты переговоров', 0)
            title.alignment = WD_ALIGN_PARAGRAPH.CENTER

            results_text = self.current_results_text

            for line in results_text.split('\n'):
                paragraph = doc.add_paragraph()
                run = paragraph.add_run(line)
                run.font.size = Pt(12)

            doc.save(file_path)
            messagebox.showinfo("Успех", f"Отчёт успешно сохранён:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить отчёт:\n{str(e)}")

    # --- Логика работы с данными и обновлением UI ---

    def update_scenario_list(self):
        """Обновление списка сценариев"""
        scenarios = list_available_scenarios()
        if scenarios:
            self.scenario_listbox.configure(values=scenarios)
            self.scenario_listbox.set(scenarios[0])
            self.on_scenario_selected(scenarios[0])
        else:
            self.scenario_listbox.configure(values=["Нет доступных сценариев"])
            self.scenario_listbox.set("Нет доступных сценариев")

    def on_scenario_selected(self, choice):
        """Обработчик выбора сценария"""
        if choice and choice != "Нет доступных сценариев":
            scenario = load_scenario_by_name(choice)
            if scenario:
                self.current_scenario = scenario
                self.scenario_info_text.configure(state="normal")
                self.scenario_info_text.delete("1.0", "end")
                self.scenario_info_text.insert("1.0", scenario.get_scenario_info())
                self.scenario_info_text.configure(state="disabled")

    def update_negotiation_interface(self):
        """Обновление интерфейса переговоров"""
        if self.negotiation_engine:
            self.round_label.configure(text=f"Раунд {self.negotiation_engine.round_count}")

        if self.last_user_offer:
            self.user_offer_textbox.configure(state="normal")
            self.user_offer_textbox.delete("1.0", "end")
            self.user_offer_textbox.insert("1.0", format_dict(self.last_user_offer, 1))
            self.user_offer_textbox.configure(state="disabled")
        else:
            self.user_offer_textbox.configure(state="normal")
            self.user_offer_textbox.delete("1.0", "end")
            self.user_offer_textbox.configure(state="disabled")

        if self.negotiation_engine.last_offer:
            self.agent_offer_textbox.configure(state="normal")
            self.agent_offer_textbox.delete("1.0", "end")
            self.agent_offer_textbox.insert("1.0", format_dict(self.negotiation_engine.last_offer, 1))
            self.agent_offer_textbox.configure(state="disabled")

    def show_agent_response(self, title: str, message: str):
        """Показ ответа агента"""
        self.response_textbox.configure(state="normal")
        self.response_textbox.delete("1.0", "end")
        self.response_textbox.insert("1.0", f"👤 {title}\n{message}")
        self.response_textbox.configure(state="disabled")

    def show_hint(self, hint: str):
        """Показ подсказки"""
        self.hints_textbox.configure(state="normal")
        self.hints_textbox.delete("1.0", "end")
        self.hints_textbox.insert("1.0", hint)
        self.hints_textbox.configure(state="disabled")

    def process_offer(self):
        us_acceptable = self.negotiation_engine.agent_a.is_acceptable(self.negotiation_engine.last_offer)

        if not us_acceptable:
            response = (
                f"⚠️ Это предложение невыгодно нашей стороне.\n"
                f"Наши минимальные условия (BATNA):\n{format_dict(self.current_scenario.seller.batna, 1)}\n"
                f"Пожалуйста, пересмотрите ваше предложение."
            )
            self.show_agent_response("Система", response)
            return

        them_acceptable = self.negotiation_engine.agent_b.is_acceptable(self.negotiation_engine.last_offer)

        if not them_acceptable:
            counter = self.negotiation_engine.make_counter_offer(
                self.negotiation_engine.last_offer,
                self.current_scenario.buyer
            )
            self.negotiation_engine.last_offer = counter
            self.negotiation_engine.add_to_history(
                self.current_scenario.buyer.name,
                "контрпредложил",
                counter
            )
            self.update_negotiation_interface()

            response = (
                f"❌ Наше руководство не может согласиться с этим предложением.\n"
                f"Наши минимальные условия (BATNA):\n{format_dict(self.current_scenario.buyer.batna, 1)}\n"
                f"Мы предлагаем рассмотреть встречное предложение:\n{format_dict(counter, 1)}"
            )
            self.show_agent_response(self.current_scenario.buyer.name, response)
            self.negotiation_engine.round_count += 1
            self.update_negotiation_interface()
            return

        self.show_agent_response(
            self.current_scenario.seller.name,
            "✅ Отлично! Это предложение нас полностью устраивает. Сделка заключена!"
        )
        self.end_negotiation_with_result()

    # --- Действия пользователя ---

    def make_offer_dialog(self):
        """Диалог создания предложения"""
        if not self.is_negotiation_active:
            return

        dialog = OfferDialog(self, self.current_scenario.config.items)
        self.wait_window(dialog)

        if dialog.result:
            self.last_user_offer = dialog.result.copy()
            current_offer = dialog.result
            self.negotiation_engine.last_offer = current_offer
            self.negotiation_engine.add_to_history("Пользователь", "предложил", current_offer)
            self.process_offer()

    def ask_question_dialog(self):
        """Диалог задания вопроса"""
        if not self.is_negotiation_active:
            return

        dialog = QuestionDialog(self)
        self.wait_window(dialog)

        if dialog.result:
            question_asked = dialog.result
            self.negotiation_engine.add_to_history("Пользователь", f"спросил: {question_asked}")

            agent = self.current_scenario.buyer
            agent_name = agent.name

            if "фактор" in question_asked.lower() or "важн" in question_asked.lower():
                if agent.weights:
                    sorted_params = sorted(agent.weights.items(), key=lambda item: item[1], reverse=True)
                    most_important_param = sorted_params[0][0] if sorted_params else "основные параметры"
                    readable_param = localize(most_important_param)
                    answer = f"Для нас ключевым фактором является {readable_param}. Мы стремимся найти баланс, но это направление для нас приоритетно."
                else:
                    answer = "Для нас важны все аспекты сделки. Мы хотим найти наиболее сбалансированное решение."

            elif "бюджет" in question_asked.lower() or "ограничения" in question_asked.lower():
                price_weight = agent.weights.get("price", 0)
                if price_weight > 0.6:
                    answer = "Бюджет является для нас критичным ограничением. Мы работаем в рамках строго определённого финансирования."
                elif 0.3 <= price_weight <= 0.6:
                    answer = "У нас есть определённый бюджетный коридор. В рамках него мы готовы обсуждать гибкие условия по другим параметрам."
                else:
                    answer = "Бюджет не является главным ограничением. Мы можем рассмотреть варианты с чуть большей инвестицией ради качества или сроков."

            elif "срочн" in question_asked.lower() or "реализац" in question_asked.lower():
                deadline_weight = agent.weights.get("deadline", 0)
                if deadline_weight > 0.6:
                    answer = "Срочность крайне высока. Нам необходимо завершить проект в ближайшие сроки, это критично для нашего бизнес-процесса."
                elif 0.3 <= deadline_weight <= 0.6:
                    answer = "Проект имеет определённые временные рамки. Мы хотели бы уложиться в согласованный график, но готовы обсудить небольшие сдвиги."
                else:
                    answer = "Сроки важны, но у нас есть некоторая гибкость. Мы можем рассмотреть варианты, если это компенсируется другими преимуществами."

            elif "альтернатив" in question_asked.lower() or "рассматриваете" in question_asked.lower():
                answer = "Мы изучили несколько вариантов на рынке. Ваше предложение конкурентоспособно, и мы заинтересованы в продуктивных переговорах."

            elif "качеств" in question_asked.lower() or "решен" in question_asked.lower():
                quality_weight = agent.weights.get("quality", 0)
                if quality_weight > 0.6:
                    answer = "Качество для нас является приоритетом номер один. Мы не готовы идти на компромиссы в этой области, так как это напрямую влияет на нашу репутацию и эффективность."
                elif 0.3 <= quality_weight <= 0.6:
                    answer = "Качество имеет для нас большое значение. Мы стремимся к высокому стандарту, но готовы обсудить баланс с другими параметрами."
                else:
                    answer = "В данном случае мы можем рассмотреть варианты с разным уровнем детализации."

            elif "гибкость" in question_asked.lower() or "срокам" in question_asked.lower() or "цене" in question_asked.lower():
                price_weight = agent.weights.get("price", 0)
                deadline_weight = agent.weights.get("deadline", 0)
                if price_weight < 0.7 and deadline_weight < 0.7:
                    answer = "Мы открыты к обсуждению гибких условий. Возможно, компромисс по одному параметру позволит улучшить другой."
                else:
                    if price_weight > 0.7:
                        answer = "Нам очень важно уложиться в бюджет, поэтому по цене гибкость минимальна. Однако по срокам мы можем посмотреть."
                    else:
                        answer = "Сроки для нас критичны, это жёсткое требование. Но в части цены мы готовы рассмотреть варианты."
            else:
                answer = "Это важный вопрос. Мы хотим найти решение, которое устроит обе стороны. Давайте сосредоточимся на предложении, которое учитывает ключевые интересы."

            self.show_agent_response(agent_name, answer)
            self.negotiation_engine.add_to_history(
                agent_name,
                "ответил",
                {"question": question_asked, "answer": answer}
            )

    def get_hint(self):
        """Получение подсказки"""
        if not self.negotiation_engine.hint_system or not self.negotiation_engine.hint_system.can_give_hint():
            self.show_hint("💡 Подсказки исчерпаны или недоступны.")
            return

        hint = self.negotiation_engine.hint_system.get_general_hint()
        self.show_hint(hint)

    def accept_offer(self):
        """Принятие текущего предложения"""
        if not self.is_negotiation_active or not self.negotiation_engine.last_offer:
            self.show_agent_response("Система", "Нет предложения для принятия")
            return

        self.process_offer()

    def end_negotiation(self):
        """Завершение переговоров без сделки"""
        self.is_negotiation_active = False
        self.negotiation_engine.last_offer = None

        result_text = "🏁 ПЕРЕГОВОРЫ ЗАВЕРШЕНЫ\n"
        result_text += f"Сценарий: {self.current_scenario.config.title}\n"
        result_text += f"Раундов проведено: {self.negotiation_engine.round_count}\n"
        result_text += "❌ Переговоры завершены без заключения сделки\n"
        result_text += "📝 Причина: Пользователь завершил переговоры\n"

        self.show_results(result_text)

    def end_negotiation_with_result(self):
        """Завершение переговоров с результатом"""
        self.is_negotiation_active = False
        print(self.negotiation_engine.history)
        self.show_results()

    def show_results(self, custom_message: str = None):
        """Показ результатов переговоров"""
        if custom_message:
            result_text = custom_message
        else:
            result_text = self.negotiation_engine.generate_result(self.current_scenario.config.title)
            self.current_results_text = result_text

        self.results_textbox.configure(state="normal")
        self.results_textbox.delete("1.0", "end")
        self.results_textbox.insert("1.0", result_text)
        self.results_textbox.configure(state="disabled")

        self.show_view("results")

    def load_scenario_from_file(self):
        """Загрузка сценария из файла"""
        file_path = filedialog.askopenfilename(
            title="Выберите файл сценария",
            filetypes=[("SCN files", "*.scn"), ("All files", "*.*")]
        )

        if file_path:
            scenario = ScenarioLoader.load_from_json(file_path)
            if scenario:
                self.current_scenario = scenario
                self.scenario_info_text.configure(state="normal")
                self.scenario_info_text.delete("1.0", "end")
                self.scenario_info_text.insert("1.0", scenario.get_scenario_info())
                self.scenario_info_text.configure(state="disabled")
                messagebox.showinfo("Успех", "Сценарий успешно загружен!")
            else:
                messagebox.showerror("Ошибка", "Не удалось загрузить сценарий")


# --- Диалоговые окна ---

class OfferDialog(ctk.CTkToplevel):
    """Диалог создания предложения"""

    def __init__(self, parent, items):
        super().__init__(parent)
        self.title("Создание предложения")
        self.geometry("500x400")
        self.geometry("+200+250")
        self.resizable(False, False)

        # Применяем тему к окну диалога
        self.configure(fg_color=theme.current_theme_data["colors"]["bg_primary"])

        self.transient(parent)
        self.grab_set()

        self.items = items
        self.result = None
        self.entries = {}

        self.create_widgets()

    def create_widgets(self):
        """Создание виджетов диалога"""
        title_label = ctk.CTkLabel(
            self,
            text="📝 Создание предложения",
            **get_label_style('secondary', 'xl')
        )
        title_label.pack(pady=20)

        params_frame = ctk.CTkScrollableFrame(self, width=450, height=200, **get_frame_style("secondary"))
        params_frame.pack(pady=10, padx=20, fill="both", expand=True)

        for item in self.items:
            frame = ctk.CTkFrame(params_frame, fg_color="transparent")
            frame.pack(fill="x", pady=5)

            label_text = ""
            if item == "price":
                label_text = "Цена (руб.)"
            elif item == "deadline":
                label_text = "Срок поставки (дней)"
            elif item == "quality":
                label_text = "Качество (1-5)"
            elif item == "warranty":
                label_text = "Гарантия (1-10)"
            else:
                label_text = item.capitalize()

            ctk.CTkLabel(frame, text=label_text, width=150, **get_label_style('primary', 'sm')).pack(side="left", padx=5)

            vcmd = (frame.register(is_valid_float_input if ROUNDING[item] > 0 else is_valid_int_input), '%P')
            entry = ctk.CTkEntry(frame, width=200, validate='key', validatecommand=vcmd, **theme.get_widget_style("entry", "primary", "md"))
            entry.pack(side="right", padx=5)
            self.entries[item] = entry

        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=20)

        ok_button = ctk.CTkButton(
            button_frame,
            **get_button_style('primary', 'md'),
            text="✅ Создать",
            command=self.ok,
        )
        ok_button.pack(side="left", padx=10)

        cancel_button = ctk.CTkButton(
            button_frame,
            **get_button_style('tertiary', 'md'),
            text="❌ Отмена",
            command=self.cancel,
        )
        cancel_button.pack(side="left", padx=10)

    def ok(self):
        """Обработка нажатия OK"""
        try:
            offer = {}
            for item, entry in self.entries.items():
                value = entry.get().strip().replace(",", ".")
                if not value:
                    raise ValueError(f'Поле "{localize(item)}" не заполнено')
                if item == "price":
                    price = int(value)
                    if price < 1:
                        raise ValueError("Цена не может меньше рубля")
                    offer[item] = price
                elif item == "deadline":
                    deadline = int(value)
                    if deadline < 1:
                        raise ValueError("Нельзя договориться на выполнения задания в прошлом")
                    offer[item] = deadline
                elif item == "quality":
                    quality = float(value)
                    if not 1 <= quality <= 5:
                        raise ValueError("Качество должно быть от 1 до 5")
                    offer[item] = quality
                else:
                    temp_item = float(value)
                    if not 0 <= temp_item <= 10:
                        raise ValueError(f"Значение {temp_item} должно быть от 0 до 10")
                    offer[item] = temp_item

            self.result = offer
            self.destroy()
        except ValueError as e:
            messagebox.showerror("Ошибка", f"Неверный формат: {str(e)}")

    def cancel(self):
        """Обработка нажатия Cancel"""
        self.result = None
        self.destroy()


class QuestionDialog(ctk.CTkToplevel):
    """Диалог задания вопроса"""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Задать вопрос")
        self.geometry("500x250")
        self.geometry("+200+250")
        self.resizable(False, False)

        self.configure(fg_color=theme.current_theme_data["colors"]["bg_secondary"])

        self.transient(parent)
        self.grab_set()

        self.result = None

        self.create_widgets()

    def create_widgets(self):
        """Создание виджетов диалога"""
        title_label = ctk.CTkLabel(
            self,
            text="❓ Задать вопрос",
            **get_label_style('primary', 'xl')
        )
        title_label
        title_label.pack(pady=20)

        questions = [
            "Какой фактор для вас наиболее важен?",
            "Есть ли у вас ограничения по бюджету?",
            "Насколько срочна реализация проекта?",
            "Какие альтернативы вы рассматриваете?",
            "Как вы оцениваете качество предлагаемого решения?",
            "Можем ли мы обсудить гибкость по срокам или цене?"
        ]

        self.question_var = ctk.StringVar(value=questions[0])

        self.question_combo = ctk.CTkComboBox(
            self,
            values=questions,
            variable=self.question_var,
            width=450,
            **get_entry_style('md')
        )
        self.question_combo.pack(pady=20)

        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=20)

        ok_button = ctk.CTkButton(
            button_frame,
            **get_button_style('primary', 'md'),
            text="✅ Отправить",
            command=self.ok,
        )
        ok_button.pack(side="left", padx=10)

        cancel_button = ctk.CTkButton(
            button_frame,
            **get_button_style('tertiary', 'md'),
            text="❌ Отмена",
            command=self.cancel,
        )
        cancel_button.pack(side="left", padx=10)

    def ok(self):
        """Обработка нажатия OK"""
        self.result = self.question_var.get()
        self.destroy()

    def cancel(self):
        """Обработка нажатия Cancel"""
        self.result = None
        self.destroy()


def is_valid_float_input(s: str) -> bool:
    if s == "":
        return True
    if s == "." or s == ",":
        return True
    s = s.replace(',', '.')
    if s.count('.') > 1:
        return False
    try:
        float(s)
        return True
    except ValueError:
        return False

def is_valid_int_input(s: str) -> bool:
    if s == "":
        return True
    if not s.isdigit():
        return False
    try:
        int(s)
        return True
    except ValueError:
        return False

def main():
    """Главная функция приложения"""
    app = NegotiationGUI()
    app.mainloop()


if __name__ == "__main__":
    main()