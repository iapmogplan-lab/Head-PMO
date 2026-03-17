import sqlite3
from datetime import datetime

DATABASE_NAME = 'project_manager.db'

def init_db():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            created_at TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'A Fazer',
            due_date TEXT,
            assigned_to TEXT,
            created_at TEXT,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
    ''')
    conn.commit()
    conn.close()

def add_project(name, description=None):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        created_at = datetime.now().isoformat()
        cursor.execute("INSERT INTO projects (name, description, created_at) VALUES (?, ?, ?)",
                       (name, description, created_at))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None # Project with this name already exists
    finally:
        conn.close()

def get_projects():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description, created_at FROM projects")
    projects = [{'id': row[0], 'name': row[1], 'description': row[2], 'created_at': row[3]}
                for row in cursor.fetchall()]
    conn.close()
    return projects

def get_project_by_name(name):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description, created_at FROM projects WHERE name = ?", (name,))
    project = cursor.fetchone()
    conn.close()
    if project:
        return {'id': project[0], 'name': project[1], 'description': project[2], 'created_at': project[3]}
    return None

def get_project_by_id(project_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description, created_at FROM projects WHERE id = ?", (project_id,))
    project = cursor.fetchone()
    conn.close()
    if project:
        return {'id': project[0], 'name': project[1], 'description': project[2], 'created_at': project[3]}
    return None

def update_project(project_id, name=None, description=None):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    updates = []
    params = []
    if name:
        updates.append("name = ?")
        params.append(name)
    if description:
        updates.append("description = ?")
        params.append(description)
    
    if not updates:
        conn.close()
        return False

    params.append(project_id)
    cursor.execute(f"UPDATE projects SET {', '.join(updates)} WHERE id = ?", tuple(params))
    conn.commit()
    conn.close()
    return True

def delete_project(project_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE project_id = ?", (project_id,))
    cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()
    return True

def add_task(project_id, description, status='A Fazer', due_date=None, assigned_to=None):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    created_at = datetime.now().isoformat()
    cursor.execute("INSERT INTO tasks (project_id, description, status, due_date, assigned_to, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                   (project_id, description, status, due_date, assigned_to, created_at))
    conn.commit()
    conn.close()
    return cursor.lastrowid

def get_tasks(project_id=None):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    if project_id:
        cursor.execute("SELECT id, project_id, description, status, due_date, assigned_to, created_at FROM tasks WHERE project_id = ?", (project_id,))
    else:
        cursor.execute("SELECT id, project_id, description, status, due_date, assigned_to, created_at FROM tasks")
    tasks = [{'id': row[0], 'project_id': row[1], 'description': row[2], 'status': row[3], 'due_date': row[4], 'assigned_to': row[5], 'created_at': row[6]}
             for row in cursor.fetchall()]
    conn.close()
    return tasks

def get_task_by_id(task_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, project_id, description, status, due_date, assigned_to, created_at FROM tasks WHERE id = ?", (task_id,))
    task = cursor.fetchone()
    conn.close()
    if task:
        return {'id': task[0], 'project_id': task[1], 'description': task[2], 'status': task[3], 'due_date': task[4], 'assigned_to': task[5], 'created_at': task[6]}
    return None

def update_task(task_id, description=None, status=None, due_date=None, assigned_to=None):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    updates = []
    params = []
    if description:
        updates.append("description = ?")
        params.append(description)
    if status:
        updates.append("status = ?")
        params.append(status)
    if due_date:
        updates.append("due_date = ?")
        params.append(due_date)
    if assigned_to:
        updates.append("assigned_to = ?")
        params.append(assigned_to)
    
    if not updates:
        conn.close()
        return False

    params.append(task_id)
    cursor.execute(f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?", tuple(params))
    conn.commit()
    conn.close()
    return True

def delete_task(task_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return True
