from database.connection import get_connection


def get_all_participants():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM participants
        WHERE active = 1
        ORDER BY first_name
    """)

    participants = cursor.fetchall()

    conn.close()

    return participants


def get_participant_by_id(participant_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM participants
        WHERE id = ?
    """, (participant_id,))

    participant = cursor.fetchone()

    conn.close()

    return participant


def initialize_database():

    conn = get_connection()
    cursor = conn.cursor()

    # ==========================================
    # TABLA DE PARTICIPANTES
    # ==========================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS participants (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            first_name TEXT NOT NULL,

            last_name TEXT NOT NULL,

            age INTEGER NOT NULL,

            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            active INTEGER DEFAULT 1

        )
    """)

    # ==========================================
    # TABLA DE SESIONES
    # ==========================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            participant_id INTEGER NOT NULL,

            session_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            status TEXT DEFAULT 'active',

            FOREIGN KEY (participant_id)
                REFERENCES participants(id)

        )
    """)

    # ==========================================
    # COMPATIBILIDAD CON BASES EXISTENTES
    # ==========================================

    # Si la tabla sessions ya existía antes de agregar
    # la columna status, la agregamos automáticamente.

    cursor.execute("PRAGMA table_info(sessions)")

    columns = [column[1] for column in cursor.fetchall()]

    if "status" not in columns:

        cursor.execute("""
            ALTER TABLE sessions
            ADD COLUMN status TEXT DEFAULT 'active'
        """)

    conn.commit()
    conn.close()


def create_participant(first_name, last_name, age):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO participants
        (
            first_name,
            last_name,
            age
        )

        VALUES
        (
            ?, ?, ?
        )
    """, (first_name, last_name, age))

    conn.commit()
    conn.close()


def delete_participant(participant_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE participants
        SET active = 0
        WHERE id = ?
    """, (participant_id,))

    conn.commit()
    conn.close()


# ==================================================
# SESIONES
# ==================================================


def get_session_count(participant_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM sessions
        WHERE participant_id = ?
        AND status = 'active'
    """, (participant_id,))

    result = cursor.fetchone()

    conn.close()

    return result[0]


def register_session(participant_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO sessions
        (
            participant_id,
            status
        )

        VALUES
        (
            ?,
            'active'
        )
    """, (participant_id,))

    conn.commit()
    conn.close()


def cancel_last_session(participant_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id
        FROM sessions
        WHERE participant_id = ?
        AND status = 'active'
        ORDER BY session_date DESC, id DESC
        LIMIT 1
    """, (participant_id,))

    session = cursor.fetchone()

    if session is None:

        conn.close()

        return False

    session_id = session[0]

    cursor.execute("""
        UPDATE sessions
        SET status = 'cancelled'
        WHERE id = ?
    """, (session_id,))

    conn.commit()
    conn.close()

    return True

def get_session_history(participant_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            session_date,
            status
        FROM sessions
        WHERE participant_id = ?
        ORDER BY session_date DESC, id DESC
    """, (participant_id,))

    sessions = cursor.fetchall()

    conn.close()

    return sessions

def delete_session(session_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM sessions
        WHERE id = ?
    """, (session_id,))

    conn.commit()
    conn.close()