from app import create_app, db
from app.models import DailyLog, InterventionFeedback, User
from datetime import datetime, timedelta

def inject():
    app = create_app()
    with app.app_context():
        user = User.query.first()
        if not user:
            user = User(username='test_student')
            db.session.add(user)
            db.session.commit()
            
        # Target: Yesterday
        yesterday = datetime.utcnow().date()
        
        # Check if log exists
        existing = DailyLog.query.filter_by(user_id=user.id, date=yesterday).first()
        if existing:
            print(f"Log for {yesterday} already exists. Deleting feedback to force check-in.")
            feedback = InterventionFeedback.query.filter_by(daily_log_id=existing.id).first()
            if feedback:
                db.session.delete(feedback)
                db.session.commit()
                print("Feedback deleted. Morning Check-In should be active.")
            return

        # Create high-usage log
        log = DailyLog(
            user_id=user.id,
            date=yesterday,
            total_screen_hours=6.5,
            target_bedtime="23:00",
            tiktok_ig_hours=2.5,  # High usage to trigger specific analysis
            youtube_hours=0.0,
            other_socials_hours=0.0,
            gaming_hours=4.0, # High gaming triggers Morning Check-In
            academic_hours_after_bedtime=0.0,
            pickups_after_bedtime=2,
            risk_score=85.0,
            risk_level="High"
        )
        
        db.session.add(log)
        db.session.commit()
        print(f"Injected log for {yesterday} with high Gaming/TikTok usage.")
        print("Go to Dashboard -> 'Morning Check-In' should be visible.")

if __name__ == "__main__":
    inject()
