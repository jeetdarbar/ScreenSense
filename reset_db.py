from app import create_app, db
from app.models import DailyLog, InterventionFeedback

app = create_app()

with app.app_context():
    try:
        # Delete child records first to avoid foreign key constraint errors
        num_feedback = db.session.query(InterventionFeedback).delete()
        print(f"Deleted {num_feedback} feedback entries.")

        # Delete parent records
        num_logs = db.session.query(DailyLog).delete()
        print(f"Deleted {num_logs} daily logs.")

        db.session.commit()
        print("Database reset successfully. All charts and logs are cleared.")
    except Exception as e:
        db.session.rollback()
        print(f"Error resetting database: {e}")
