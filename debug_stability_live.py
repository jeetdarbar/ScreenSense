from app import create_app, db
from app.models import DailyLog
from app.services.risk_engine import RiskEngine
import statistics

def debug_stability():
    app = create_app()
    with app.app_context():
        # Get last 7 logs
        user_id = 1
        logs = DailyLog.query.filter_by(user_id=user_id).order_by(DailyLog.date.desc()).limit(7).all()
        
        print(f"Found {len(logs)} logs.")
        
        late_hours = []
        for log in logs:
            p_social = (getattr(log, 'tiktok_ig_hours', 0) or 0) + \
                       (getattr(log, 'youtube_hours', 0) or 0) + \
                       (getattr(log, 'reddit_x_hours', 0) or 0) + \
                       (getattr(log, 'gaming_hours', 0) or 0)
                       
            total = p_social + log.academic_hours_after_bedtime
            
            print(f"Date: {log.date} | TikTok: {log.tiktok_ig_hours} | YouTube: {log.youtube_hours} | Reddit: {log.reddit_x_hours} | Gaming: {log.gaming_hours} | Acad: {log.academic_hours_after_bedtime} -> TOTAL Late: {total}")
            late_hours.append(total)
            
        if len(late_hours) < 2:
            print("Not enough data for stdev. Score: 100.0")
            return

        stdev = statistics.stdev(late_hours)
        print(f"\nCalculated StDev: {stdev}")
        
        stability = max(0, 100 - (stdev * 20))
        print(f"Raw Score (100 - stdev*20): {100 - (stdev * 20)}")
        print(f"Final Stability Score: {stability}")

if __name__ == "__main__":
    debug_stability()
