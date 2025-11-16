import psycopg2
import psycopg2.errors 
import time
from config import DB_CONFIG

class DatabaseModel:
    """Клас Моделі, відповідає за всю взаємодію з PostgreSQL."""

    def __init__(self):
        self.conn = None
        self.connect()

    def connect(self):
        """Встановлює підключення до бази даних."""
        try:
            db_config_lab1 = DB_CONFIG.copy()
            
            # Встановлюємо search_path через options, 
            # щоб уникнути помилок з транзакціями
            db_config_lab1['options'] = '-c search_path=lab1,public'
            
            self.conn = psycopg2.connect(**db_config_lab1)
            
            # ЯВНО вказуємо, що автокоміт вимкнено.
            # Кожна операція, що змінює дані, 
            # ПОТРЕБУВАТИМЕ .commit()
            self.conn.autocommit = False 
            
            print(" Підключення до БД (схема 'lab1') успішне.")
        
        except psycopg2.OperationalError as e:
            print(f" Помилка підключення до БД: {e}")
            self.conn = None
        except psycopg2.Error as e:
            print(f" Помилка налаштування (переконайтесь, що схема 'lab1' існує): {e}")
            self.conn = None

    def close(self):
        """Закриває підключення."""
        if self.conn:
            self.conn.close()
            
    # --- CRUD ДЛЯ CLIENT ---
    
    def insert_client(self, firstname, lastname, email, phone):
        """[CREATE] Вставляє новий запис Client."""
        sql = """
            INSERT INTO client (client_first_name, client_last_name, client_email, client_phone)
            VALUES (%s, %s, %s, %s) 
            RETURNING client_id;
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, (firstname, lastname, email, phone))
                client_id = cur.fetchone()[0] 
                self.conn.commit() # Зберігаємо зміни
                return client_id
        except psycopg2.Error as e:
            self.conn.rollback() # Відкочуємо у разі помилки
            return f"Помилка БД: {e.diag.message_primary}"
            
    def select_all_clients(self):
        """[READ] Вибирає всі записи (обмежено 100)."""
        sql = "SELECT client_id, client_first_name, client_last_name, client_email, client_phone FROM client LIMIT 100;"
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql)
                headers = [desc.name for desc in cur.description] 
                data = cur.fetchall()
                # SELECT не потребує commit
                return headers, data
        except psycopg2.Error as e:
            return None, f"Помилка БД: {e.diag.message_primary}"
            
    def update_client(self, client_id, firstname, lastname, email, phone):
        """[UPDATE] Оновлює запис Client."""
        sql = """
            UPDATE client SET 
                client_first_name = %s, client_last_name = %s, client_email = %s, client_phone = %s
            WHERE client_id = %s;
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, (firstname, lastname, email, phone, client_id))
                if cur.rowcount == 0:
                    self.conn.rollback() # Нічого не оновлено, відкат
                    return f"Клієнт з ID {client_id} не знайдений."
                self.conn.commit() # Зберігаємо
                return f" Клієнт з ID {client_id} успішно оновлений."
        except psycopg2.Error as e:
            self.conn.rollback()
            return f"Помилка БД: {e.diag.message_primary}"

    def delete_client(self, client_id):
        """[DELETE] Видаляє запис Client з контролем цілісності."""
        sql = "DELETE FROM client WHERE client_id = %s;"
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, (client_id,))
                if cur.rowcount == 0:
                    self.conn.rollback() # Нічого не видалено
                    return f"Клієнт з ID {client_id} не знайдений."
                self.conn.commit() # Зберігаємо
                return f" Клієнт з ID {client_id} успішно видалений."
        
        # Це виконання Пункту 1 РГР
        except psycopg2.errors.ForeignKeyViolation as e:
            self.conn.rollback() # КРИТИЧНО: відкат, якщо не можна видалити
            return f" Помилка БД: Неможливо видалити клієнта {client_id}, оскільки він має активні бронювання (FK Violation)!"
        except psycopg2.Error as e:
            self.conn.rollback()
            return f"Помилка БД: {e.diag.message_primary}"

    # --- ГЕНЕРАЦІЯ ДАНИХ (Пункт 2) ---
    
    def generate_buildings_and_facilities(self, count=10):
        """Генерує FK-таблиці для цілісності Booking."""
        building_sql = f"INSERT INTO building (building_name, building_address) SELECT 'Gym ' || t.i, 'Street ' || t.i FROM generate_series(1, {count}) AS t(i);"
        facility_sql = f"INSERT INTO facility (building_id, facility_number, max_capacity, price_per_hour) SELECT (random() * ({count}-1) + 1)::int, t.i, (random() * 50 + 10)::int, (random() * 200 + 100)::int FROM generate_series(1, 100) AS t(i);"
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(building_sql)
                cur.execute(facility_sql)
            self.conn.commit() # Зберігаємо
            return f" Додано {count} будівель та 100 приміщень для цілісності."
        except psycopg2.Error as e:
            self.conn.rollback()
            return f" Помилка БД під час генерації FK-таблиць: {e.diag.message_primary}"

    def generate_clients(self, count):
        """Генерує count псевдовипадкових записів у таблицю Client."""
        sql = f"""
            INSERT INTO client (client_first_name, client_last_name, client_email, client_phone)
            SELECT 
                first_name.name, last_name.name,
                LOWER(first_name.name) || '.' || LOWER(last_name.name) || floor(random() * 1000) :: int || '@sportbook.com',
                '380' || (100000000 + floor(random() * 899999999)) :: bigint
            FROM 
                generate_series(1, {count}) AS t(i) 
                CROSS JOIN LATERAL (SELECT name FROM (VALUES ('Oleksandr'), ('Dmytro'), ('Yana')) AS names(name) ORDER BY random() LIMIT 1) AS first_name
                CROSS JOIN LATERAL (SELECT name FROM (VALUES ('Shevchenko'), ('Kovalenko'), ('Melnyk')) AS names(name) ORDER BY random() LIMIT 1) AS last_name;
        """
        try:
            start_time = time.time() 
            with self.conn.cursor() as cur:
                cur.execute(sql)
            self.conn.commit() # Зберігаємо
            end_time = time.time()
            
            time_ms = round((end_time - start_time) * 1000, 2)
            return f" {count} записів додано до Client. Час виконання: {time_ms} мс."

        except psycopg2.Error as e:
            self.conn.rollback()
            return f" Помилка БД під час генерації: {e.diag.message_primary}"

    def _get_max_ids(self):
        """Отримує реальні максимальні ID для коректної генерації FK."""
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT MAX(client_id) FROM client;")
                max_client_id = cur.fetchone()[0]
                
                cur.execute("SELECT MAX(facility_id) FROM facility;")
                max_facility_id = cur.fetchone()[0]
                
                if not max_client_id or not max_facility_id:
                    self.conn.rollback() # Не знайшли ID, відкат
                    return None, None
                return max_client_id, max_facility_id
        except psycopg2.Error:
            self.conn.rollback() 
            return None, None

    def generate_bookings(self, count):
        """Генерує count псевдовипадкових бронювань (Booking)."""
        
        max_client, max_facility = self._get_max_ids()
        if not max_client or not max_facility:
            return " Помилка: Необхідно спочатку згенерувати Клієнтів та Приміщення (FK порушення)!"

        sql = f"""
            INSERT INTO booking (client_id, facility_id, start_time, end_time, status)
            SELECT
                (random() * ({max_client} - 1) + 1)::int AS client_id, 
                (random() * ({max_facility} - 1) + 1)::int AS facility_id, 
                TIMESTAMP '2025-01-01 08:00:00' + (random() * (INTERVAL '365 days')) AS start_time,
                (TIMESTAMP '2025-01-01 08:00:00' + (random() * (INTERVAL '365 days'))) + (random() * 3 + 1) * INTERVAL '1 hour' AS end_time,
                CASE 
                    WHEN random() < 0.8 THEN 'confirmed'
                    WHEN random() < 0.9 THEN 'pending'
                    ELSE 'cancelled'
                END
            FROM 
                generate_series(1, {count}) AS t(i);
        """
        try:
            start_time = time.time()
            with self.conn.cursor() as cur:
                cur.execute(sql)
            self.conn.commit() # Зберігаємо
            end_time = time.time()
            
            time_ms = round((end_time - start_time) * 1000, 2)
            return f" {count} записів додано до Booking. Час виконання: {time_ms} мс."

        except psycopg2.errors.ForeignKeyViolation as e:
            self.conn.rollback()
            return f" Помилка FK (це дивно, перевірте _get_max_ids): {e.diag.message_primary}"
        except psycopg2.Error as e:
            self.conn.rollback()
            return f" Помилка БД під час генерації Booking: {e.diag.message_primary}"


    # --- ПОШУК (Пункт 3) ---

    def search_bookings(self, facility_id, date_from, date_to, status, min_price):
        """Реалізація пошуку за декількома атрибутами з 3-х сутностей."""
        
        sql = """
            SELECT
                C.client_first_name, C.client_last_name, 
                F.facility_number, F.price_per_hour, 
                B.start_time, B.end_time, B.status
            FROM 
                booking B
            JOIN 
                client C ON B.client_id = C.client_id
            JOIN 
                facility F ON B.facility_id = F.facility_id
        """
        
        params = []
        where_clauses = []
        
        if status:
            where_clauses.append("B.status ILIKE %s") 
            params.append(f'%{status}%')

        if min_price:
            where_clauses.append("F.price_per_hour >= %s")
            params.append(min_price)

        if facility_id:
            where_clauses.append("F.facility_id = %s")
            params.append(facility_id)
            
        if date_from and date_to:
            where_clauses.append("B.start_time BETWEEN %s AND %s")
            params.append(date_from)
            params.append(date_to)
        elif date_from:
            where_clauses.append("B.start_time >= %s")
            params.append(date_from)
        elif date_to:
            where_clauses.append("B.start_time <= %s")
            params.append(date_to)

        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)
            
        sql += " LIMIT 50;"

        try:
            start_time = time.time()
            with self.conn.cursor() as cur:
                cur.execute(sql, tuple(params))
                headers = [desc.name for desc in cur.description] 
                data = cur.fetchall()
            end_time = time.time()
            
            # SELECT не потребує commit
            
            time_ms = round((end_time - start_time) * 1000, 2)
            
            return f" Пошук завершено. Знайдено {len(data)} записів. Час виконання: {time_ms} мс.", (headers, data)

        except psycopg2.Error as e:
            self.conn.rollback() # На випадок помилки SELECT
            return f" Помилка БД під час пошуку: {e.diag.message_primary}", (None, None)