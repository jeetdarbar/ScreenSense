from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from . import db
from .models import User, DailyLog, InterventionFeedback, AppCategoryMap
from .services.risk_engine import RiskEngine
from .services.insight_engine import InsightEngine
from .services.analytics import AnalyticsEngine
from datetime import datetime, timedelta
import json

main = Blueprint('main', __name__)

@main.route('/api/v1/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'message': 'ScreenSense Backend Live'}), 200

def get_current_dashboard_state(user):
    # SELF-HEALING: Ensure columns exist if accessed (Granular Recovery)
    from sqlalchemy import text
    try:
        # Check 'user' table columns
        cols_to_add_user = [
            ("target_bedtime", "VARCHAR(10) DEFAULT '23:00'"),
            ("target_wake_time", "VARCHAR(10) DEFAULT '07:00'")
        ]
        for col_name, col_def in cols_to_add_user:
            try:
                db.session.execute(text(f"ALTER TABLE user ADD COLUMN {col_name} {col_def}"))
                db.session.commit()
                print(f"[BACKEND] Added column {col_name} to user table.")
            except Exception:
                db.session.rollback() # Likely duplicate column, ignore
        
        # Check 'intervention_feedback' table columns
        try:
            db.session.execute(text("ALTER TABLE intervention_feedback ADD COLUMN actual_wake_time VARCHAR(10)"))
            db.session.commit()
            print("[BACKEND] Added column actual_wake_time to feedback table.")
        except Exception:
            db.session.rollback()
            
    except Exception as e:
        print(f"[BACKEND CRITICAL] Migration engine failed: {e}")

    now = datetime.utcnow() + timedelta(hours=5, minutes=30) #IST
    current_time_str = now.strftime('%H:%M')
    
    log = DailyLog.query.filter_by(user_id=user.id).order_by(DailyLog.date.desc()).first()
    
    # State A: Live (Danger Zone)
    is_after_bedtime = current_time_str >= user.target_bedtime
    is_before_wake = current_time_str < user.target_wake_time
    
    feedback = None
    if log:
        feedback = InterventionFeedback.query.filter_by(daily_log_id=log.id).first()
    
    if (is_after_bedtime or is_before_wake) and not feedback:
        return "live", "Tonight's Live Risk", user.target_bedtime
        
    if not log:
        # For brand new users during the day, show reflection with baseline
        return "reflection", "Getting Started", user.target_bedtime

    # State B: Pending (Waiting for Morning Report)
    if not feedback and current_time_str >= user.target_wake_time:
        return "pending", "Waiting for Perspective", user.target_bedtime
        
    # State C: Reflection (Locked Dashboard)
    return "reflection", "Last Night's Impact", user.target_bedtime

@main.route('/api/v1/auth/register', methods=['POST'])
def register():
    try:
        data = request.json
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if User.query.filter_by(email=email).first() or User.query.filter_by(username=username).first():
            return jsonify({'error': 'User already exists'}), 400
            
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        access_token = create_access_token(identity=str(new_user.id))
        return jsonify({'access_token': access_token, 'user_id': new_user.id, 'username': new_user.username}), 201
    except Exception as e:
        print(f"[AUTH ERROR] Register failed: {e}")
        return jsonify({'error': str(e)}), 500

@main.route('/api/v1/auth/login', methods=['POST'])
def login():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            access_token = create_access_token(identity=str(user.id))
            return jsonify({'access_token': access_token, 'user_id': user.id, 'username': user.username}), 200
            
        return jsonify({'error': 'Invalid email or password'}), 401
    except Exception as e:
        print(f"[AUTH ERROR] Login failed: {e}")
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@main.route('/api/v1/user/settings', methods=['GET', 'PUT'])
@jwt_required()
def user_settings():
    import traceback
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if request.method == 'PUT':
            data = request.json
            if 'username' in data: user.username = data['username']
            if 'password' in data: user.set_password(data['password'])
            if 'target_bedtime' in data: user.target_bedtime = data['target_bedtime']
            if 'target_wake_time' in data: user.target_wake_time = data['target_wake_time']
            db.session.commit()
            
        return jsonify({
            'username': user.username,
            'email': user.email,
            'target_bedtime': user.target_bedtime,
            'target_wake_time': user.target_wake_time
        }), 200
    except Exception as e:
        print(f"[BACKEND ERROR] user_settings failed: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@main.route('/api/v1/telemetry', methods=['POST'])
@jwt_required()
def sync_telemetry():
    import traceback
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user:
            print(f"[BACKEND ERROR] User not found for id={user_id}")
            return jsonify({'error': 'User not found'}), 404
        payload = request.json
        
        def format_usage(raw_list):
            formatted = []
            for item in raw_list:
                pkg_name = item.get('package', '')
                mins = item.get('minutes', 0)
                if mins <= 0 or not pkg_name: continue
                formatted.append({
                    "name": item.get('name', pkg_name.split('.')[-1].capitalize()),
                    "category": item.get('category', 'Utility'),
                    "minutes": mins
                })
            return formatted

        formatted_full = format_usage(payload.get('full_usage', []))
        formatted_risk = format_usage(payload.get('risk_usage', []))
        
        print(f"[BACKEND] Sync for user {user.id}. Apps received: {len(formatted_full)}")

        today = datetime.utcnow().date()
        print(f"[BACKEND] Querying for date={today}")
        log = DailyLog.query.filter_by(user_id=user.id, date=today).first()
        
        if not log:
            print("[BACKEND] No log found. Creating new one.")
            log = DailyLog(
                user_id=user.id, 
                date=today, 
                target_bedtime=user.target_bedtime,
                target_wake_time=user.target_wake_time,
                app_usage_json=json.dumps(formatted_full),
                risk_usage_json=json.dumps(formatted_risk),
                pickups_after_bedtime=0
            )
            db.session.add(log)
        else:
            print(f"[BACKEND] Existing log found (id={log.id}). Updating.")
            log.app_usage_json = json.dumps(formatted_full)
            log.risk_usage_json = json.dumps(formatted_risk)
            
        db.session.commit()
        print(f"[BACKEND] DB commit successful. log.id={log.id}")
        
        try:
            previous_logs = DailyLog.query.filter_by(user_id=user.id).order_by(DailyLog.date.desc()).limit(14).all()
            risk_score = RiskEngine.calculate_risk_score(log, previous_logs)
            log.risk_score = risk_score
            log.risk_level = RiskEngine.get_risk_level(risk_score)
            db.session.commit()
            print(f"[BACKEND] Risk score calculated: {risk_score}")
        except Exception as risk_err:
            print(f"[BACKEND WARNING] Risk engine failed (non-fatal): {risk_err}")
            risk_score = 0
        
        saved_count = len(formatted_full)
        print(f"[BACKEND] SUCCESS. Returning saved_count={saved_count}")
        
        return jsonify({
            'status': 'success', 
            'risk_score': risk_score,
            'saved_count': saved_count
        }), 200

    except Exception as e:
        print(f"[BACKEND CRITICAL] sync_telemetry crashed: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e), 'saved_count': -1}), 500

@main.route('/api/v1/morning_report', methods=['POST'])
@jwt_required()
def morning_report():
    try:
        user_id = int(get_jwt_identity())
        data = request.json
        latest_log = DailyLog.query.filter_by(user_id=user_id).order_by(DailyLog.date.desc(), DailyLog.id.desc()).first()
        
        if not latest_log:
            return jsonify({'error': 'No telemetry data'}), 404
            
        time_to_asleep = int(data.get('time_to_fall_asleep_mins', 0))
        groggy_score = int(data.get('morning_grogginess_score', 1))
        wake_time = data.get('actual_wake_time', '07:00')
        
        feedback = InterventionFeedback.query.filter_by(daily_log_id=latest_log.id).first()
        if not feedback:
            feedback = InterventionFeedback(
                daily_log_id=latest_log.id, 
                time_to_fall_asleep_mins=time_to_asleep, 
                morning_grogginess_score=groggy_score,
                actual_wake_time=wake_time
            )
            db.session.add(feedback)
        else:
            feedback.time_to_fall_asleep_mins = time_to_asleep
            feedback.morning_grogginess_score = groggy_score
            feedback.actual_wake_time = wake_time
        
        # 1. Fetch apps for engine
        import json
        apps = json.loads(latest_log.apps_usage_json) if latest_log.apps_usage_json else []
        
        # 2. Generate Insight from TextEngine
        analysis = InsightEngine.generate_morning_analysis(
            apps=apps,
            minutes_to_sleep=time_to_asleep,
            grogginess_score=groggy_score
        )
        
        report_data = {
            "reinforcement": analysis,
            "analysis": "Morning Circadian Assessment Complete.",
            "action_plan": "Keep consistent with your wake-up time."
        }
        
        # PERSISTENCE: Save to DB
        latest_log.report_json = json.dumps(report_data)
        db.session.commit()
        
        return jsonify({
            "status": "success", 
            "transition_message": "Impact Calculated.",
            "reinforcement": analysis
        }), 200

    except Exception as e:
        print(f"[BACKEND CRITICAL] morning_report crashed: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@main.route('/api/v1/dashboard', methods=['GET'])
@jwt_required()
def dashboard_data():
    import traceback
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        # Stricter query: get latest by date AND then by ID
        logs = DailyLog.query.filter_by(user_id=user_id).order_by(DailyLog.date.desc(), DailyLog.id.desc()).limit(7).all()
        
        # DEBUG TRACE: show all log dates in server terminal
        print(f"[DASHBOARD DEBUG] user_id={user_id}, UTC now={datetime.utcnow()}, logs found={len(logs)}")
        for l in logs:
            print(f"  -> Log id={l.id} date={l.date} app_usage_json_len={len(l.app_usage_json or '')}")
        
        stability_index = RiskEngine.calculate_stability_index(logs)
        latest = logs[0] if logs else None
        
        state, label, bedtime = get_current_dashboard_state(user)
        
        return jsonify({
            'username': user.username,
            'dashboard_state': state,
            'cycle_label': label,
            'stability_index': stability_index,
            'needs_morning_checkin': state == 'pending',
            'latest_risk_score': round(latest.risk_score, 2) if latest and latest.risk_score else 0,
            'latest_risk_level': latest.risk_level if latest else 'Unknown',
            'apps_usage': json.loads(latest.app_usage_json) if latest and latest.app_usage_json else [],
            'audio_prescription': InsightEngine.get_audio_prescription(latest) if latest else "Silence",
            'next_bedtime': bedrock_to_iso(bedtime)
        }), 200
    except Exception as e:
        print(f"[BACKEND ERROR] dashboard_data failed: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

def bedrock_to_iso(time_str):
    now = datetime.utcnow()
    return f"{now.date().isoformat()}T{time_str}:00Z"

@main.route('/api/v1/history/calendar', methods=['GET'])
@jwt_required()
def history_calendar():
    user_id = int(get_jwt_identity())
    logs = DailyLog.query.filter_by(user_id=user_id).all()
    # Return a list of ISO dates that have entries
    return jsonify([log.date.isoformat() for log in logs]), 200

@main.route('/api/v1/history/day/<date_str>', methods=['GET'])
@jwt_required()
def history_day(date_str):
    user_id = int(get_jwt_identity())
    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    log = DailyLog.query.filter_by(user_id=user_id, date=date_obj).first()
    
    if not log:
        return jsonify({'error': 'No data for this date'}), 404
        
    apps = json.loads(log.app_usage_json) if log.app_usage_json else []
    total_mins = sum([a['minutes'] for a in apps])
    most_used = max(apps, key=lambda x: x['minutes'])['name'] if apps else "None"
    
    return jsonify({
        'date': date_str,
        'total_minutes': total_mins,
        'most_used_app': most_used,
        'report': json.loads(log.report_json) if log.report_json else None,
        'risk_score': log.risk_score,
        'risk_level': log.risk_level
    }), 200

@main.route('/api/v1/history/weekly_summary', methods=['GET'])
@jwt_required()
def weekly_summary():
    user_id = int(get_jwt_identity())
    logs = DailyLog.query.filter_by(user_id=user_id).order_by(DailyLog.date.desc()).limit(7).all()
    if not logs:
        return jsonify({'error': 'Insufficient data'}), 400
        
    avg_risk = sum([log.risk_score or 0 for log in logs]) / len(logs)
    
    # Aggregate app usage across the week
    all_apps = {}
    for log in logs:
        apps = json.loads(log.app_usage_json) if log.app_usage_json else []
        for a in apps:
            all_apps[a['name']] = all_apps.get(a['name'], 0) + a['minutes']
            
    top_disruptors = sorted(all_apps.items(), key=lambda x: x[1], reverse=True)[:3]
    
    # Generate a Weekly Insight from Gemini
    # For now, we reuse the InsightEngine or create a simplified summary
    summary_text = f"Over the past 7 days, your average risk was {round(avg_risk, 1)}%. Your biggest disruptors are {', '.join([d[0] for d in top_disruptors])}."
    
    return jsonify({
        'average_risk': round(avg_risk, 2),
        'top_disruptors': top_disruptors,
        'weekly_insight': summary_text
    }), 200
