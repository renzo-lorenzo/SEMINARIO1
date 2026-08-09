from database.connection import get_connection


# ==================================================
# PARTICIPANTES
# ==================================================

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

            registration_date TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

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

            exercise_id INTEGER,

            session_date TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

            repetitions_completed INTEGER
                DEFAULT 0,

            target_repetitions INTEGER
                DEFAULT 10,

            duration_seconds INTEGER
                DEFAULT 0,

            points_earned INTEGER
                DEFAULT 0,

            status TEXT DEFAULT 'active',

            FOREIGN KEY (participant_id)
                REFERENCES participants(id)

        )
    """)

    # ==========================================
    # TABLA DE CONFIGURACIÓN DE EJERCICIOS
    # ==========================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS participant_exercises (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            participant_id INTEGER NOT NULL,

            exercise_id INTEGER NOT NULL,

            target_repetitions INTEGER NOT NULL
                DEFAULT 10,

            UNIQUE (
                participant_id,
                exercise_id
            ),

            FOREIGN KEY (participant_id)
                REFERENCES participants(id)

        )
    """)

    # ==========================================
    # COMPATIBILIDAD CON BASES EXISTENTES
    # ==========================================

    # ------------------------------------------
    # SESIONES
    # ------------------------------------------

    cursor.execute(
        "PRAGMA table_info(sessions)"
    )

    session_columns = [
        column[1]
        for column in cursor.fetchall()
    ]

    if "status" not in session_columns:

        cursor.execute("""
            ALTER TABLE sessions
            ADD COLUMN status TEXT
            DEFAULT 'active'
        """)

    if "exercise_id" not in session_columns:

        cursor.execute("""
            ALTER TABLE sessions
            ADD COLUMN exercise_id INTEGER
        """)

    if "repetitions_completed" not in session_columns:

        cursor.execute("""
            ALTER TABLE sessions
            ADD COLUMN repetitions_completed INTEGER
            DEFAULT 0
        """)

    if "target_repetitions" not in session_columns:

        cursor.execute("""
            ALTER TABLE sessions
            ADD COLUMN target_repetitions INTEGER
            DEFAULT 10
        """)

    if "duration_seconds" not in session_columns:

        cursor.execute("""
            ALTER TABLE sessions
            ADD COLUMN duration_seconds INTEGER
            DEFAULT 0
        """)

    if "points_earned" not in session_columns:

        cursor.execute("""
            ALTER TABLE sessions
            ADD COLUMN points_earned INTEGER
            DEFAULT 0
        """)

    conn.commit()
    conn.close()


def create_participant(
    first_name,
    last_name,
    age
):

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
    """, (
        first_name,
        last_name,
        age
    ))

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
# CONFIGURACIÓN DE REPETICIONES POR PARTICIPANTE
# ==================================================

def get_exercise_repetitions(
    participant_id,
    exercise_id,
    default_repetitions=10
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT target_repetitions
        FROM participant_exercises
        WHERE participant_id = ?
        AND exercise_id = ?
    """, (
        participant_id,
        exercise_id
    ))

    result = cursor.fetchone()

    # ==========================================
    # SI YA EXISTE CONFIGURACIÓN
    # ==========================================

    if result is not None:

        repetitions = result[0]

        conn.close()

        return repetitions

    # ==========================================
    # SI NO EXISTE
    # CREAR CONFIGURACIÓN POR DEFECTO
    # ==========================================

    cursor.execute("""
        INSERT INTO participant_exercises
        (
            participant_id,
            exercise_id,
            target_repetitions
        )

        VALUES
        (
            ?, ?, ?
        )
    """, (
        participant_id,
        exercise_id,
        default_repetitions
    ))

    conn.commit()
    conn.close()

    return default_repetitions


def set_exercise_repetitions(
    participant_id,
    exercise_id,
    repetitions
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO participant_exercises
        (
            participant_id,
            exercise_id,
            target_repetitions
        )

        VALUES
        (
            ?, ?, ?
        )

        ON CONFLICT (
            participant_id,
            exercise_id
        )

        DO UPDATE SET
            target_repetitions =
                excluded.target_repetitions
    """, (
        participant_id,
        exercise_id,
        repetitions
    ))

    conn.commit()
    conn.close()


def get_all_exercise_repetitions(
    participant_id
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            exercise_id,
            target_repetitions

        FROM participant_exercises

        WHERE participant_id = ?
    """, (participant_id,))

    repetitions = cursor.fetchall()

    conn.close()

    return repetitions


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
            session_date,
            status
        )
        VALUES
        (
            ?,
            CURRENT_TIMESTAMP,
            'active'
        )
    """, (participant_id,))

    # Obtener el ID de la sesión recién creada
    session_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return session_id


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

        ORDER BY
            session_date DESC,
            id DESC
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