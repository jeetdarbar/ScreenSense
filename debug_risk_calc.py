from app import create_app, db
from app.models import DailyLog
from app.services.risk_engine import RiskEngine

def debug_risk():
    app = create_app()
    with app.app_context():
        # Get all recent logs
        user_id = 1
        logs = DailyLog.query.filter_by(user_id=user_id).order_by(DailyLog.date.desc()).limit(10).all()
        
        if not logs:
            print("No logs found!")
            return
        
        print(f"\n=== All Recent Logs (Last 10) ===")
        for i, log in enumerate(logs, 1):
            total_social = (log.tiktok_ig_hours + log.youtube_hours + 
                           log.other_socials_hours + log.gaming_hours)
            
            print(f"\n--- Log #{i} | Date: {log.date} ---")
            print(f"  Risk Score: {log.risk_score}")
            print(f"  Total Social: {total_social}h | Academic: {log.academic_hours_after_bedtime}h | Pickups: {log.pickups_after_bedtime}")
            
            if log.risk_score and log.risk_score >= 99:
                print(f"  ⚠️ MAXED OUT! Social={total_social}h exceeds threshold ({RiskEngine.MAX_SOCIAL_HOURS}h)")
        
        print(f"\n=== Dashboard Data Endpoint Check ===")
        # Simulate what the dashboard-data endpoint returns
        latest_log = logs[0] if logs else None
        if latest_log:
            print(f"Latest log date: {latest_log.date}")
            print(f"Latest risk_score from DB: {latest_log.risk_score}")
            print(f"What dashboard shows: {round(latest_log.risk_score, 2) if latest_log.risk_score else 0}")

if __name__ == "__main__":
    debug_risk()
