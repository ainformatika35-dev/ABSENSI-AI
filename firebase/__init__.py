# Package initialization for firebase module
from .firebase_config import (
    get_db,
    is_firebase_connected,
    init_firebase,
    get_user,
    get_user_by_username_or_nis,
    create_or_update_user,
    delete_user,
    get_all_students,
    get_face_data,
    save_face_embeddings,
    reset_face_data,
    get_all_face_data,
    save_attendance,
    get_attendance_by_date,
    get_attendance_for_user_today,
    get_attendance_history_for_user,
    get_all_attendance_records,
    seed_default_admin
)
