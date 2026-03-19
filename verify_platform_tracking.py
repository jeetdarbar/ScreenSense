from app import create_app, db
from app.models import User, DailyLog, InterventionFeedback
from app.services.text_engine import TextEngine
from app.services.analytics import AnalyticsEngine
from datetime import datetime, timedelta
import random

app = create_app()

def setup_database():
    with app.app_context():
        print("Dropped old DB...")
        db.drop_all()
        print("Created new DB...")
        db.create_all()
        
        # Create User
        user = User(username="test_student")
        db.session.add(user)
        db.session.commit()
        print("User created.")

def populate_dummy_data():
    with app.app_context():
        user = User.query.first()
        
        # Create 10 days of logs
        platforms = ["TikTok/IG", "YouTube", "Reddit/X", "Gaming"]
        
        for i in range(10):
            date = datetime.utcnow().date() - timedelta(days=10-i)
            
            # Randomize usage
            tiktok = random.uniform(0, 3)
            youtube = random.uniform(0, 3)
            reddit = random.uniform(0, 2)
            gaming = random.uniform(0, 4)
            
            # Correlate latency with a specific platform (e.g., Gaming)
            # Make Gaming correlate with high latency
            latency = 10 + (gaming * 20) + random.randint(-5, 5)
            
            log = DailyLog(
                user_id=user.id,
                date=date,
                total_screen_hours=tiktok+youtube+reddit+gaming+1,
                target_bedtime="23:00",
                tiktok_ig_hours=tiktok,
                youtube_hours=youtube,
                reddit_x_hours=reddit,
                gaming_hours=gaming,
                academic_hours_after_bedtime=0.5,
                pickups_after_bedtime=random.randint(0, 5)
            )
            # Fake risk score calculation for speed
            log.risk_score = min((tiktok+youtube+reddit+gaming) * 10, 100)
            log.risk_level = "High" if log.risk_score > 70 else "Moderate"
            
            db.session.add(log)
            db.session.commit()
            
            # Add Feedback
            fb = InterventionFeedback(
                daily_log_id=log.id,
                time_to_fall_asleep_mins=int(latency),
                intervention_type="none"
            )
            db.session.add(fb)
            db.session.commit()
            
        print("Dummy data populated (10 days).")

def test_text_engine():
    print("\n--- Testing TextEngine ---")
    # Test TikTok High
    msg = TextEngine.generate_nightly_insight(3.0, 0.5, 0, 0)
    print(f"TikTok High Insight: {msg}")
    
    # Test Gaming High
    msg = TextEngine.generate_nightly_insight(0, 0.5, 0, 4.0)
    print(f"Gaming High Insight: {msg}")
    
    # Test Morning Analysis
    analysis = TextEngine.generate_morning_analysis(0, 0, 0, 4.0, 60)
    print(f"Morning Analysis (Gaming, 60m latency): {analysis}")

def test_insight_engine():
    print("\n--- Testing InsightEngine Integration ---")
    from app.services.insight_engine import InsightEngine
    
    # Mock Log Object
    class MockLog:
        tiktok_ig_hours = 1.5
        youtube_hours = 0.5
        other_socials_hours = 2.0 # Was Reddit/X
        gaming_hours = 1.0
        academic_hours_after_bedtime = 0.0
        pickups_after_bedtime = 2
        
    log = MockLog()
    try:
        report = InsightEngine.generate_root_cause_analysis(log, 45)
        print(f"[PASS] InsightEngine generated report: {report[:50]}...")
        
        full_report = InsightEngine.generate_morning_report(log, 45)
        print(f"[PASS] InsightEngine generated full morning report: Reinforcement='{full_report['reinforcement']}'")
    except Exception as e:
        print(f"[FAIL] InsightEngine failed: {e}")
        import traceback
        traceback.print_exc()

def test_risk_engine():
    print("\n--- Testing RiskEngine (Stability) ---")
    from app.services.risk_engine import RiskEngine
    from app.models import DailyLog
    
    # Fetch recent logs (populated in dummy data)
    with app.app_context():
        logs = DailyLog.query.all()
        try:
            stability = RiskEngine.calculate_stability_index(logs)
            print(f"[PASS] Stability Index Calculated: {stability}")
        except Exception as e:
            print(f"[FAIL] Stability Calculation Failed: {e}")
            import traceback
            traceback.print_exc()

def test_analytics():
    print("\n--- Testing Analytics ---")
    with app.app_context():
        user = User.query.first()
        analysis = AnalyticsEngine.calculate_behavioral_correlations(user.id)
        
        expected_keys = ["tiktok_hours", "youtube_hours", "reddit_hours", "gaming_hours", "academic_hours", "pickups"]
        print(f"Keys present: {list(analysis.keys())}")
        
        missing = [k for k in expected_keys if k not in analysis]
        if missing:
            print(f"[FAIL] Missing keys in analytics: {missing}")
        else:
            print("[PASS] All analytics keys present.")
            
        print("Gaming Correlation Score:", analysis.get('gaming_hours', {}).get('score'))

def test_dashboard_data():
    print("\n--- Testing Dashboard Data Endpoint ---")
    with app.test_client() as client:
        response = client.get('/dashboard-data')
        if response.status_code == 200:
            data = response.get_json()
            score = data.get('latest_risk_score')
            print(f"[PASS] Dashboard Data received. Latest Score: {score}")
            if score is not None:
                # content check for rounding
                if isinstance(score, float) and len(str(score).split('.')[-1]) > 2:
                     print(f"[FAIL] Score {score} is not rounded to 2 decimal places.")
                else:
                     print(f"[PASS] Score {score} is properly rounded.")
            else:
                print("[FAIL] latest_risk_score is MISSING or None.")
        else:
            print(f"[FAIL] /dashboard-data failed with {response.status_code}")

if __name__ == "__main__":
    setup_database()
    populate_dummy_data()
    test_text_engine()
    test_insight_engine()
    test_risk_engine()
    test_analytics()
    test_dashboard_data()
