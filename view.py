# view.py

from datetime import datetime

class ConsoleView:
    """Відповідає за відображення та отримання введення (print/input)."""
    
    def show_message(self, message):
        """Виводить повідомлення."""
        print(message)

    def show_main_menu(self):
        """Головне меню."""
        print("\n" + "="*40)
        print("      ОНЛАЙН-ПЛАТФОРМА БРОНЮВАННЯ")
        print("="*40)
        print("1. CRUD Операції (Робота з таблицями)")
        print("2. Генерація Даних (100k)")
        print("3. Пошук та Фільтрація")
        print("0. Вихід")
        return input(">>> Оберіть дію: ")

    def show_table_menu(self):
        """Меню вибору таблиці."""
        print("\n--- Оберіть таблицю ---")
        print("1. Клієнти (Client)")
        print("2. Бронювання (Booking)")
        print("3. Будівлі (Building)")
        print("4. Приміщення (Facility)")
        print("5. Адміністратори (Administrator)")
        print("0. Назад")
        return input(">>> Ваш вибір: ")

    def show_crud_menu(self, table_name):
        """Меню дій для конкретної таблиці."""
        print(f"\n--- CRUD Меню: {table_name} ---")
        print("1. [R] Переглянути всі записи (Limit 100)")
        print("2. [C] Додати новий запис")
        print("3. [U] Редагувати запис (за ID)")
        print("4. [D] Видалити запис (за ID)")
        print("9. Назад")
        return input(">>> Оберіть дію: ")
        
    # --- ФОРМИ ВВЕДЕННЯ ДАНИХ ---

    def get_client_data(self, is_update=False):
        """Зчитує дані для Клієнта."""
        title = "Оновлення" if is_update else "Створення"
        print(f"\n--- {title} Клієнта ---")
        firstname = input("Ім'я: ")
        lastname = input("Прізвище: ")
        email = input("Email: ")
        phone = input("Телефон: ")
        
        if not all([firstname, lastname, email, phone]):
            self.show_message("❌ Помилка: Усі поля обов'язкові.")
            return None
        return firstname, lastname, email, phone

    def get_booking_data(self):
        """Зчитує дані для Бронювання."""
        print("\n--- Створення/Оновлення Бронювання ---")
        try:
            client_id = int(input("ID Клієнта: "))
            facility_id = int(input("ID Приміщення: "))
            start_str = input("Початок (YYYY-MM-DD HH:MM:SS): ")
            end_str = input("Кінець (YYYY-MM-DD HH:MM:SS): ")
            status = input("Статус (confirmed/pending/cancelled): ")
            
            # Проста перевірка дати (необов'язково, але бажано)
            # datetime.strptime(start_str, '%Y-%m-%d %H:%M:%S')
            
            return client_id, facility_id, start_str, end_str, status
        except ValueError:
            self.show_message("❌ Помилка: ID мають бути числами, дати у коректному форматі.")
            return None

    def get_id(self, action="дії"):
        """Запитує ID запису."""
        try:
            val = input(f">>> Введіть ID запису для {action}: ")
            return int(val)
        except ValueError:
            self.show_message("❌ Помилка: ID має бути числом.")
            return None

    def get_generation_count(self):
        """Запитує кількість для генерації."""
        try:
            val = input(">>> Введіть кількість записів (напр. 100000): ")
            count = int(val)
            if count <= 0: raise ValueError
            return count
        except ValueError:
            self.show_message("❌ Помилка: введіть ціле число > 0.")
            return None

    def show_data(self, headers, data):
        """Відображає дані у вигляді таблиці."""
        if not data:
            self.show_message("— Не знайдено жодних записів. —")
            return

        # Вираховуємо ширину колонок
        col_widths = [len(str(h)) for h in headers]
        for row in data:
            for i, item in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(item)))

        # Форматування
        row_format = " | ".join([f"{{:<{w}}}" for w in col_widths])
        separator = "-+-".join(["-" * w for w in col_widths])

        print("\n" + separator)
        print(row_format.format(*headers))
        print(separator)
        
        for row in data:
            # Обробка None та конвертація в стрічку
            formatted_row = [str(item) if item is not None else "NULL" for item in row]
            print(row_format.format(*formatted_row))
        print(separator + "\n")

    def get_search_params(self):
        """Зчитує параметри для пошуку."""
        print("\n--- Пошук та Фільтрація (Пункт 3) ---")
        status = input("Статус (або частина, наприклад 'conf'): ")
        
        date_from_str = input("Дата від (YYYY-MM-DD) [Enter=пропустити]: ")
        date_to_str = input("Дата до (YYYY-MM-DD) [Enter=пропустити]: ")
        
        facility_id_str = input("ID Приміщення [Enter=пропустити]: ")
        min_price_str = input("Мін. ціна за годину [Enter=пропустити]: ")
        
        try:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date() if date_from_str else None
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date() if date_to_str else None
            facility_id = int(facility_id_str) if facility_id_str else None
            min_price = int(min_price_str) if min_price_str else None
            
            return facility_id, date_from, date_to, status, min_price
        except ValueError:
            self.show_message("❌ Помилка вводу: Перевірте формат дати або чисел.")
            return None