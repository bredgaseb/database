# controller.py

from model import DatabaseModel
from view import ConsoleView
import time

class MainController:
    """Керує потоком програми."""

    def __init__(self):
        self.model = DatabaseModel()
        self.view = ConsoleView()

    def run(self):
        """Головний цикл програми."""
        if not self.model.conn:
            self.view.show_message("Програму неможливо запустити без підключення до БД.")
            return

        while True:
            choice = self.view.show_main_menu()
            
            if choice == '1':
                self._handle_crud()
            elif choice == '2':
                self._handle_generation_menu()
            elif choice == '3':
                self._handle_search() # Викликаємо обробник пошуку
            elif choice == '0':
                self.model.close()
                self.view.show_message("Додаток закрито. До побачення!")
                break
            else:
                self.view.show_message("Невірний вибір. Спробуйте ще раз.")

    def _handle_crud(self):
        """Обробка CRUD для таблиці Client."""
        while True:
            crud_choice = self.view.show_crud_menu(table_name="Клієнти (Client)")
            
            if crud_choice == '1': # READ
                headers, data = self.model.select_all_clients()
                if headers:
                    self.view.show_data(headers, data)
                else:
                    self.view.show_message(data)

            elif crud_choice == '2': # CREATE
                data = self.view.get_new_client_data()
                if data:
                    firstname, lastname, email, phone = data
                    result = self.model.insert_client(firstname, lastname, email, phone)
                    if isinstance(result, int):
                        self.view.show_message(f"✅ Клієнт успішно доданий (ID: {result}).")
                    else:
                        self.view.show_message(f"❌ Помилка при додаванні клієнта: {result}")
                        
            elif crud_choice == '3': # UPDATE
                client_id = self.view.get_id_for_action("редагування")
                if client_id is not None:
                    data = self.view.get_new_client_data(client_id)
                    if data:
                        firstname, lastname, email, phone = data
                        result = self.model.update_client(client_id, firstname, lastname, email, phone)
                        self.view.show_message(result)

            elif crud_choice == '4': # DELETE
                client_id = self.view.get_id_for_action("видалення")
                if client_id is not None:
                    result = self.model.delete_client(client_id)
                    self.view.show_message(result)
                    
            elif crud_choice == '9':
                break
            else:
                self.view.show_message("Невірний вибір. Спробуйте ще раз.")
                
    def _handle_generation_menu(self):
        """Обробка генерації даних."""
        self.view.show_message("\n--- Генерація Даних (Пункт 2) ---")
        self.view.show_message("1. Створити Будівлі та Приміщення (FK-таблиці) [10 / 100]")
        self.view.show_message("2. Згенерувати 100 000 Клієнтів")
        self.view.show_message("3. Згенерувати 100 000 Бронювань")
        
        gen_choice = input(">>> Оберіть дію: ")
        
        if gen_choice == '1':
             result = self.model.generate_buildings_and_facilities()
             self.view.show_message(result)
        elif gen_choice == '2':
            count = self.view.get_generation_count()
            if count:
                result = self.model.generate_clients(count)
                self.view.show_message(result)
        elif gen_choice == '3':
            count = self.view.get_generation_count()
            if count:
                result = self.model.generate_bookings(count)
                self.view.show_message(result)
        else:
            self.view.show_message("Невірний вибір.")

    def _handle_search(self):
        """Обробка складного пошуку (Пункт 3)."""
        
        # 1. Отримати параметри пошуку від View
        params = self.view.get_search_params()
        if params is None:
            return

        facility_id, date_from, date_to, status, min_price = params

        # 2. Викликати Model для виконання запиту
        result_msg, (headers, data) = self.model.search_bookings(
            facility_id, date_from, date_to, status, min_price
        )
        
        # 3. Показати повідомлення та результат
        self.view.show_message(result_msg)
        if headers:
            self.view.show_data(headers, data)


if __name__ == "__main__":
    app = MainController()
    app.run()