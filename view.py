# view.py

from datetime import datetime

class ConsoleView:
    """Відповідає за відображення та отримання введення (print/input)."""
    
    def show_message(self, message):
        """Виводить загальні повідомлення."""
        print(message)

    def show_main_menu(self):
        """Виводить головне меню та повертає вибір користувача."""
        print("\n" + "="*40)
        print("      ОНЛАЙН-ПЛАТФОРМА БРОНЮВАННЯ")
        print("="*40)
        print("1. CRUD Операції (Клієнт)")
        print("2. Генерація Даних (100k)")
        print("3. Пошук та Фільтрація")
        print("0. Вихід")
        return input(">>> Оберіть дію: ")

    def show_crud_menu(self, table_name="Клієнти"):
        """Меню для CRUD операцій."""
        print(f"\n--- CRUD Меню ({table_name}) ---")
        print("1. [R] Переглянути 100 записів")
        print("2. [C] Додати новий запис")
        print("3. [U] Редагувати запис (за ID)")
        print("4. [D] Видалити запис (за ID)")
        print("9. Назад до головного меню")
        return input(">>> Оберіть дію: ")
        
    def get_new_client_data(self, client_id=None):
        """Зчитує дані для нового/оновленого клієнта."""
        if client_id is None:
            print("\n--- Введення даних Клієнта ---")
        else:
            print(f"\n--- Редагування Клієнта ID: {client_id} ---")
            
        firstname = input("Ім'я: ")
        lastname = input("Прізвище: ")
        email = input("Email: ")
        phone = input("Телефон (рядковий): ")
        
        if not all([firstname, lastname, email, phone]):
            self.show_message("❌ Усі поля є обов'язковими (NOT NULL).")
            return None

        return firstname, lastname, email, phone
        
    def get_generation_count(self):
        """Запитує кількість записів для генерації."""
        while True:
            count_str = input(">>> Введіть кількість записів для генерації (наприклад, 100000): ")
            try:
                count = int(count_str)
                if count <= 0:
                     self.show_message("❌ Кількість має бути більше 0.")
                     continue
                return count
            except ValueError:
                self.show_message("❌ Невірний формат. Введіть ціле число.")
                return None
                
    def get_id_for_action(self, action="редагування"):
        """Запитує ID для оновлення або видалення."""
        while True:
            id_str = input(f">>> Введіть ID запису для {action}: ")
            try:
                return int(id_str)
            except ValueError:
                self.show_message("❌ ID має бути числом.")

    def show_data(self, headers, data):
        """Форматує та виводить дані у вигляді простої таблиці."""
        if not data:
            self.show_message("— Не знайдено жодних записів. —")
            return

        col_widths = [len(h) for h in headers]
        for row in data:
            for i, item in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(item)))

        row_format = "".join([f"{{:<{w + 3}}}" for w in col_widths])
        
        print("\n" + "=" * (sum(col_widths) + len(col_widths) * 3))
        print(row_format.format(*headers))
        print("—" * (sum(col_widths) + len(col_widths) * 3))
        
        for row in data:
            print(row_format.format(*[str(item) for item in row]))
        print("=" * (sum(col_widths) + len(col_widths) * 3))
        
    def get_search_params(self):
        """Отримує параметри для складного пошуку."""
        print("\n--- Введення параметрів Пошуку (Пункт 3) ---")
        
        # Приклад збору даних (можна розширити)
        status = input("Введіть статус бронювання (або частину, наприклад 'conf'): ")
        
        # Дати (складна валідація опускається для стислості)
        date_from_str = input("Дата початку бронювання (YYYY-MM-DD) (залиште пустим, якщо не потрібно): ")
        date_to_str = input("Дата кінця бронювання (YYYY-MM-DD) (залиште пустим, якщо не потрібно): ")
        
        try:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d') if date_from_str else None
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d') if date_to_str else None
        except ValueError:
            self.show_message("❌ Невірний формат дати. Використовуйте YYYY-MM-DD.")
            return None, None, None, None, None
            
        # Заглушки для інших параметрів, які потрібно збирати:
        facility_id = input("ID Приміщення (число, залиште пустим): ")
        min_price = input("Мінімальна ціна за годину (число, залиште пустим): ")

        return (
            int(facility_id) if facility_id.isdigit() else None, 
            date_from, 
            date_to, 
            status if status else None, 
            int(min_price) if min_price.isdigit() else None
        )