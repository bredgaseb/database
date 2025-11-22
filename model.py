# model.py

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
            # Копіюємо конфігурацію, щоб не змінювати оригінал
            cfg = DB_CONFIG.copy()
            # Встановлюємо search_path, щоб не писати 'lab1.' перед кожною таблицею
            cfg['options'] = '-c search_path=lab1,public'
            
            self.conn = psycopg2.connect(**cfg)
            self.conn.autocommit = False # Вимикаємо автокоміт для контролю транзакцій
            print("Підключення до БД успішне.")
        except Exception as e:
            print(f"Помилка підключення: {e}")
            self.conn = None

    def close(self):
        """Закриває підключення."""
        if self.conn:
            self.conn.close()

    # =========================================================================
    # УНІВЕРСАЛЬНІ МЕТОДИ (READ, DELETE)
    # =========================================================================

    def get_all(self, table_name, limit=100):
        """
        Універсальний метод для отримання всіх записів з будь-якої таблиці.
        """
        # Увага: table_name тут підставляється через f-string. 
        # У реальному продакшені це небезпечно (SQL Injection), 
        # але для навчальної роботи та внутрішнього використання - допустимо, 
        # оскільки назва таблиці береться з hardcoded словника в контролері.
        sql = f"SELECT * FROM {table_name} LIMIT %s"
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, (limit,))
                # Отримуємо назви колонок
                headers = [desc.name for desc in cur.description]
                data = cur.fetchall()
                return headers, data
        except psycopg2.Error as e:
            return None, f"Помилка БД: {e.diag.message_primary}"

    def delete_record(self, table_name, pk_column, pk_value):
        """
        Універсальний метод для видалення запису за ID.
        """
        sql = f"DELETE FROM {table_name} WHERE {pk_column} = %s"
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, (pk_value,))
                if cur.rowcount == 0:
                    self.conn.rollback()
                    return f"Запис з ID {pk_value} не знайдено в таблиці {table_name}."
                self.conn.commit()
                return f"Запис ID {pk_value} успішно видалено з {table_name}."
        
        # Обробка помилки Foreign Key (Пункт 1 РГР)
        except psycopg2.errors.ForeignKeyViolation:
            self.conn.rollback()
            return f"Неможливо видалити запис {pk_value}: на нього посилаються інші дані (обмеження Foreign Key)!"
        except psycopg2.Error as e:
            self.conn.rollback()
            return f"Помилка БД: {e.diag.message_primary}"

    # =========================================================================
    # СПЕЦИФІЧНІ МЕТОДИ (CREATE, UPDATE)
    # =========================================================================

    # --- CLIENT ---
    def insert_client(self, data):
        """Вставка клієнта: (firstname, lastname, email, phone)"""
        sql = """
            INSERT INTO client (client_first_name, client_last_name, client_email, client_phone) 
            VALUES (%s, %s, %s, %s) 
            RETURNING client_id;
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, data)
                new_id = cur.fetchone()[0]
                self.conn.commit()
                return f"Клієнт успішно доданий (ID: {new_id})."
        except psycopg2.Error as e:
            self.conn.rollback()
            return f"Помилка додавання: {e.diag.message_primary}"

    def update_client(self, client_id, data):
        """Оновлення клієнта."""
        sql = """
            UPDATE client SET 
                client_first_name=%s, client_last_name=%s, client_email=%s, client_phone=%s 
            WHERE client_id=%s;
        """
        try:
            with self.conn.cursor() as cur:
                # Додаємо ID в кінець кортежу параметрів
                cur.execute(sql, data + (client_id,))
                if cur.rowcount == 0:
                    self.conn.rollback()
                    return "Клієнт не знайдений."
                self.conn.commit()
                return "Дані клієнта оновлено."
        except psycopg2.Error as e:
            self.conn.rollback()
            return f"Помилка оновлення: {e.diag.message_primary}"

    # --- BOOKING ---
    def insert_booking(self, data):
        """Вставка бронювання: (client_id, facility_id, start, end, status)"""
        sql = """
            INSERT INTO booking (client_id, facility_id, start_time, end_time, status) 
            VALUES (%s, %s, %s, %s, %s) 
            RETURNING booking_id;
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, data)
                new_id = cur.fetchone()[0]
                self.conn.commit()
                return f"Бронювання створено (ID: {new_id})."
        except psycopg2.errors.ForeignKeyViolation:
            self.conn.rollback()
            return "Помилка: Клієнта або Приміщення з таким ID не існує."
        except psycopg2.Error as e:
            self.conn.rollback()
            return f"Помилка БД: {e.diag.message_primary}"

    def update_booking(self, booking_id, data):
        """Оновлення бронювання."""
        sql = """
            UPDATE booking SET 
                client_id=%s, facility_id=%s, start_time=%s, end_time=%s, status=%s 
            WHERE booking_id=%s;
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, data + (booking_id,))
                self.conn.commit()
                return "Бронювання оновлено."
        except psycopg2.Error as e:
            self.conn.rollback()
            return f"Помилка: {e.diag.message_primary}"

    # =========================================================================
    # ГЕНЕРАЦІЯ ДАНИХ (Пункт 2)
    # =========================================================================

    def generate_buildings_and_facilities(self):
        """Створює базові будівлі та приміщення (якщо їх немає або мало)."""
        try:
            with self.conn.cursor() as cur:
                # Генеруємо 10 будівель
                cur.execute("""
                    INSERT INTO building (building_name, building_address) 
                    SELECT 'Gym ' || i, 'Street ' || i 
                    FROM generate_series(1, 10) AS t(i);
                """)
                # Генеруємо 100 приміщень, прив'язаних до цих будівель випадково
                # (random() * 9 + 1)::int генерує ID будівлі від 1 до 10 (якщо вони йдуть підряд)
                # Краще прив'язуватися до реальних ID, але для спрощення генерації припустимо, що Building ID є.
                cur.execute("""
                    INSERT INTO facility (building_id, facility_number, max_capacity, price_per_hour) 
                    SELECT 
                        (random() * 9 + 1)::int, 
                        i, 
                        (random() * 50 + 10)::int, 
                        (random() * 200 + 100)::int 
                    FROM generate_series(1, 100) AS t(i);
                """)
            self.conn.commit()
            return "Згенеровано 10 будівель та 100 приміщень."
        except psycopg2.errors.ForeignKeyViolation:
            self.conn.rollback()
            return "Помилка FK: Схоже, немає відповідних Building ID."
        except psycopg2.Error as e:
            self.conn.rollback()
            return f"Помилка генерації: {e.diag.message_primary}"

    def generate_clients(self, count):
        """Генерує клієнтів."""
        sql = f"""
            INSERT INTO client (client_first_name, client_last_name, client_email, client_phone)
            SELECT 
                'Name' || i, 
                'Surname' || i,
                'user' || i || '@example.com',
                '050' || floor(random() * 8999999 + 1000000)::int
            FROM generate_series(1, {count}) AS t(i);
        """
        try:
            t_start = time.time()
            with self.conn.cursor() as cur:
                cur.execute(sql)
            self.conn.commit()
            t_end = time.time()
            return f"{count} клієнтів згенеровано за {round((t_end-t_start)*1000, 2)} мс."
        except psycopg2.Error as e:
            self.conn.rollback()
            return f"Помилка генерації клієнтів: {e.diag.message_primary}"

    def generate_bookings(self, count):
        """Генерує бронювання, використовуючи існуючі ID клієнтів та приміщень."""
        # Цей запит обирає випадковий ID з таблиці client та facility для кожного нового рядка
        sql = f"""
            INSERT INTO booking (client_id, facility_id, start_time, end_time, status)
            SELECT
                (SELECT client_id FROM client ORDER BY random() LIMIT 1),
                (SELECT facility_id FROM facility ORDER BY random() LIMIT 1),
                NOW() + (random() * (INTERVAL '90 days')),
                NOW() + (random() * (INTERVAL '90 days')) + '2 hours',
                CASE WHEN random() < 0.8 THEN 'confirmed' ELSE 'cancelled' END
            FROM generate_series(1, {count}) AS t(i);
        """
        try:
            t_start = time.time()
            with self.conn.cursor() as cur:
                cur.execute(sql)
            self.conn.commit()
            t_end = time.time()
            return f"{count} бронювань згенеровано за {round((t_end-t_start)*1000, 2)} мс."
        except psycopg2.Error as e:
            self.conn.rollback()
            return f"Помилка генерації бронювань: {e.diag.message_primary}"

    # =========================================================================
    # ПОШУК (Пункт 3)
    # =========================================================================

    def search_bookings(self, facility_id, date_from, date_to, status, min_price):
        """Складний пошук із JOIN трьох таблиць."""
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
            
        sql += " LIMIT 50;" # Обмеження виводу

        try:
            start_time = time.time()
            with self.conn.cursor() as cur:
                cur.execute(sql, tuple(params))
                headers = [desc.name for desc in cur.description] 
                data = cur.fetchall()
            end_time = time.time()
            
            time_ms = round((end_time - start_time) * 1000, 2)
            msg = f"Пошук завершено. Знайдено {len(data)} записів. Час: {time_ms} мс."
            return msg, (headers, data)

        except psycopg2.Error as e:
            self.conn.rollback()
            return f"Помилка пошуку: {e.diag.message_primary}", (None, None)