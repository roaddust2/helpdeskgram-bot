import sqlite3
from datetime import datetime
import logging


DB_FILE = "helpdeskgram.db"


def insert_user(chat_id, first_name, phone_number, locale):
    """Insert user into database,
    returns created user id"""

    logging.info("Creating user...")
    conn = sqlite3.connect(DB_FILE, isolation_level=None)
    conn.execute('pragma journal_mode=wal')
    conn.execute('pragma foreign_keys=on')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (chat_id, first_name, phone_number, locale, created_at) VALUES (?, ?, ?, ?, ?)",
        (chat_id, first_name, phone_number, locale, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    user_id = cursor.lastrowid
    conn.commit()
    logging.info(f"User with id {user_id} was created")
    conn.close()
    return user_id


def get_user_id(chat_id):
    """Get user id by chat_id"""

    conn = sqlite3.connect(DB_FILE, isolation_level=None)
    conn.execute('pragma journal_mode=wal')
    conn.execute('pragma foreign_keys=on')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE chat_id = ?', (chat_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return user
    else:
        logging.info(f"User with chat_id {chat_id} was not found")
        return None


def get_user_contact(chat_id):
    """Get user contact by chat_id"""

    conn = sqlite3.connect(DB_FILE, isolation_level=None)
    conn.execute('pragma journal_mode=wal')
    conn.execute('pragma foreign_keys=on')
    cursor = conn.cursor()
    cursor.execute('SELECT first_name, phone_number FROM users WHERE chat_id = ?', (chat_id,))
    contact = cursor.fetchone()
    conn.close()
    if contact:
        return contact
    else:
        logging.info(f"User with chat_id {chat_id} was not found")
        return None


def insert_issue(user_id, issue_key):
    """Insert issue with user_id and issue_key"""

    status = "new"

    conn = sqlite3.connect(DB_FILE, isolation_level=None)
    conn.execute('pragma journal_mode=wal')
    conn.execute('pragma foreign_keys=on')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO issues (user_id, issue_key, status, created_at) VALUES (?, ?, ?, ?)",
        (user_id, issue_key, status, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    issue_id = cursor.lastrowid
    conn.commit()
    logging.info(f"Issue with id {issue_id} was created")
    conn.close()
    return


def get_issue(issue_key):
    """Get issue by issue_key"""

    conn = sqlite3.connect(DB_FILE, isolation_level=None)
    conn.execute('pragma journal_mode=wal')
    conn.execute('pragma foreign_keys=on')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT users.chat_id, issues.status, users.locale
        FROM issues
        JOIN users ON issues.user_id = users.id
        WHERE issues.issue_key = ?
    ''', (issue_key,))
    result = cursor.fetchone()
    conn.close()
    return result


def get_issues(chat_id, completed=False):
    """Get issues for specified user"""

    conn = sqlite3.connect(DB_FILE, isolation_level=None)
    conn.execute('pragma journal_mode=wal')
    conn.execute('pragma foreign_keys=on')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT issues.issue_key, issues.status, issues.created_at
        FROM issues
        JOIN users ON issues.user_id = users.id
        WHERE users.chat_id = ?
    ''', (chat_id,))
    issues = cursor.fetchall()
    conn.close()
    if completed:
        return issues
    else:
        result = [issue for issue in issues if issue[1] != "done"]
        return result


def update_issue_status(issue_key, status):
    """Update issue status by issue_key"""

    conn = sqlite3.connect(DB_FILE, isolation_level=None)
    conn.execute('pragma journal_mode=wal')
    conn.execute('pragma foreign_keys=on')
    cursor = conn.cursor()
    cursor.execute("UPDATE issues SET status = ? WHERE issue_key = ?", (status, issue_key))
    conn.commit()
    logging.info(f"Issue {issue_key} status was updated to {status}")
    conn.close()
    return
