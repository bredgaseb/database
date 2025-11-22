# controller.py

from model import DatabaseModel
from view import ConsoleView

class MainController:
    """Керує потоком програми."""

    def __init__(self):
        self.model = DatabaseModel()
        self.view = ConsoleView()
        
        # Конфігурація таблиць: 'Номер меню': ('назва_таблиці_в_БД', 'ім'я_pk_колонки')
        self.tables = {
            '1': ('client', 'client_id'),
            '2': ('booking', 'booking_id'),
            '3': ('building', 'building_id'),
            '4': ('facility', 'facility_id'),
            '5': ('administrator', 'adm_id')
        }

    def run(self):
        """Запуск головного циклу."""
        if not self.model.conn:
            self.view.show_message("Критична помилка: Немає з'єднання з БД.")
            return

        while True:
            choice = self.view.show_main_menu()
            
            if choice == '1':
                self._handle_crud_router()
            elif choice == '2':
                self._handle_gen()
            elif choice == '3':
                self._handle_search()
            elif choice == '0':
                self.model.close()
                self.view.show_message("До побачення!")
                break
            else:
                self.view.show_message("Невірний вибір.")

    def _handle_crud_router(self):
        """Підменю вибору таблиці для CRUD."""
        while True:
            t_choice = self.view.show_table_menu()
            if t_choice == '0': 
                break
            
            if t_choice not in self.tables:
                self.view.show_message("Невірний вибір таблиці.")
                continue
                
            table_name, pk_col = self.tables[t_choice]
            self._process_table_crud(t_choice, table_name, pk_col)

    def _process_table_crud(self, t_choice, table_name, pk_col):
        """Виконує CRUD операції для обраної таблиці."""
        while True:
            action = self.view.show_crud_menu(table_name)
            
            if action == '9': 
                break # Назад
            
            # 1. READ (Універсально для всіх таблиць)
            if action == '1':
                headers, data = self.model.get_all(table_name)
                if headers:
                    self.view.show_data(headers, data)
                else:
                    self.view.show_message(data) # Повідомлення про помилку

            # 2. CREATE (Специфічно для кожної таблиці)
            elif action == '2':
                if t_choice == '1': # Client
                    data = self.view.get_client_data()
                    if data:
                        self.view.show_message(self.model.insert_client(data))
                elif t_choice == '2': # Booking
                    data = self.view.get_booking_data()
                    if data:
                        self.view.show_message(self.model.insert_booking(data))
                else:
                    self.view.show_message("⚠️ Додавання для цієї таблиці реалізується аналогічно (див. код).")

            # 3. UPDATE (Специфічно для кожної таблиці)
            elif action == '3':
                rec_id = self.view.get_id("редагування")
                if rec_id:
                    if t_choice == '1': # Client
                        data = self.view.get_client_data(is_update=True)
                        if data:
                            self.view.show_message(self.model.update_client(rec_id, data))
                    elif t_choice == '2': # Booking
                        data = self.view.get_booking_data()
                        if data:
                            self.view.show_message(self.model.update_booking(rec_id, data))
                    else:
                        self.view.show_message("⚠️ Редагування для цієї таблиці реалізується аналогічно.")

            # 4. DELETE (Універсально для всіх таблиць)
            elif action == '4':
                rec_id = self.view.get_id("видалення")
                if rec_id:
                    msg = self.model.delete_record(table_name, pk_col, rec_id)
                    self.view.show_message(msg)
            
            else:
                self.view.show_message("Невірний вибір.")

    def _handle_gen(self):
        """Обробка генерації даних."""
        self.view.show_message("\n--- Генерація Даних ---")
        self.view.show_message("1. Базові дані (Будівлі та Приміщення)")
        self.view.show_message("2. Клієнти (напр. 100 000)")
        self.view.show_message("3. Бронювання (напр. 100 000)")
        
        gc = input(">>> Оберіть дію: ")
        
        if gc == '1':
            self.view.show_message(self.model.generate_buildings_and_facilities())
        elif gc == '2':
            count = self.view.get_generation_count()
            if count:
                self.view.show_message(self.model.generate_clients(count))
        elif gc == '3':
            count = self.view.get_generation_count()
            if count:
                self.view.show_message(self.model.generate_bookings(count))
        else:
            self.view.show_message("Невірний вибір.")

    def _handle_search(self):
        """Обробка пошуку."""
        params = self.view.get_search_params()
        if params:
            # Розпаковка кортежу параметрів
            facility_id, date_from, date_to, status, min_price = params
            
            msg, (headers, data) = self.model.search_bookings(
                facility_id, date_from, date_to, status, min_price
            )
            
            self.view.show_message(msg)
            if headers and data:
                self.view.show_data(headers, data)

if __name__ == "__main__":
    app = MainController()
    app.run()