import sqlite3


class BotDB:
    def __init__(self, db_file):
        """Соединение с БД"""
        self.connection = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()
    
    def user_exists(self, user_id):
        """Проверка есть ли пользователь в БД"""
        result = self.cursor.execute(
            "SELECT id FROM users WHERE user_id = ?", (user_id,)
        )
        return bool(len(result.fetchall()))
    
    def get_user_id(self, user_id):
        """Получение id пользователя в БД по user_id в telegram"""
        result = self.cursor.execute(
            "SELECT id FROM users WHERE user_id = ?", (user_id,)
        )
        return result.fetchall()[0][0]
    
    def add_user(self, user_id):
        """Добавление нового пользователя в БД"""
        self.cursor.execute(
            "INSERT INTO users (user_id) VALUES (?)", (user_id,)
        )
        return self.connection.commit()
    
    def del_user(self, user_id):
        """Удаление пользователя и всех его записей из БД"""
        self.cursor.execute(
            "DELETE FROM users WHERE user_id = ?", (user_id,)
        )
        return self.connection.commit()
    
    def add_task(self, user_id, title, date, description):
        """Добавление новой задачи"""
        self.cursor.execute(
            "INSERT INTO tasks (users_id, title, description, planned_date) "
            "VALUES (%s, '%s', '%s', date('%s'))"
            % (self.get_user_id(user_id), title, description, date)
        )
        return self.connection.commit()

    def del_task(self, task_id):
        """Удаление задачи"""
        self.cursor.execute(
            "DELETE FROM tasks WHERE id = ?", (task_id,)
        )
        return self.connection.commit()

    def complete_task(self, task_id):
        """Изменение статуса задачи на выполнено"""
        self.cursor.execute(
            "UPDATE tasks SET status = 1 WHERE id = ?", (task_id,)
        )
        return self.connection.commit()

    def replan_task(self, task_id, date):
        """Перенести задачу на другой день"""
        self.cursor.execute(
            "UPDATE tasks SET planned_date = date('%s') WHERE id = %s" % (date, task_id)
        )
        return self.connection.commit()

    def get_tasks(self, user_id, date):
        """Получение списка задач на выбранный день"""
        data = self.cursor.execute(
            "SELECT * FROM tasks WHERE users_id = %s AND DATE(planned_date) = date('%s')"
            % (self.get_user_id(user_id), date)
        )
        return data.fetchall()
    
    def get_all_tasks(self, user_id):
        """Получение полного списка невыполненных задач"""
        data = self.cursor.execute(
            "SELECT * FROM tasks WHERE users_id = %s AND status = 0 ORDER BY planned_date"
            % (self.get_user_id(user_id))
        )
        return data.fetchall()

    def close(self):
        """Закрытие соединения с БД"""
        self.connection.close()