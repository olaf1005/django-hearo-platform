def reset_database_connection():
    # helper function to reset database connection
    from django import db

    db.close_old_connections()
