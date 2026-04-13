from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from . import db
from .models import User, DailyLog, InterventionFeedback, AppCategoryMap
from .services.risk_engine import RiskEngine
from .services.insight_engine import InsightEngine
from datetime import datetime
import json

main = Blueprint('main', __name__)

@main.route('/api/v1/auth/register', methods=['POST'])
def register():
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

@main.route('/api/v1/auth/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password):
        access_token = create_access_token(identity=str(user.id))
        return jsonify({'access_token': access_token, 'user_id': user.id, 'username': user.username}), 200
        
    return jsonify({'error': 'Invalid email or password'}), 401

@main.route('/api/v1/telemetry', methods=['POST'])
@jwt_required()
def sync_telemetry():
    """Receives raw Android Package Usage Data and dynamically categorizes it"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    raw_data = request.json # Expecting [{"package": "com.instagram.android", "minutes": 81}, ...]
    
    if raw_data is None or not isinstance(raw_data, list):
        # We can accept an empty list if there's no screen time, but it must be a list
        return jsonify({'error': 'Invalid payload map, expected list of objects'}), 400

    today = datetime.utcnow().date()
    log = DailyLog.query.filter_by(user_id=user.id, date=today).first()
    
    formatted_apps = []
    
    for item in raw_data:
        pkg_name = item.get('package', '')
        mins = item.get('minutes', 0)
        
        # We skip apps that have 0 usage minutes natively
        if mins <= 0 or not pkg_name: 
            continue
            
        # Dynamic Lookup in our new Backend Logic
        category_map = AppCategoryMap.query.filter_by(package_name=pkg_name).first()
        if category_map:
            category = category_map.category
            readable = category_map.readable_name
        else:
            # Fallback for apps not explicitly in the AppCategoryMap (e.g. system apps, unknown apps)
            category = "Game" if "game" in pkg_name.lower() else "Other"
            readable = pkg_name.split('.')[-1].capitalize() # Quick humanizing heuristic

        # For analysis, we send only Social Media and Game to the UI, 
        # but realistically we can append them all.
        if category in ["Social Media", "Game"]:
            formatted_apps.append({
                "name": readable,
                "category": category,
                "minutes": mins
            })

    if not log:
        # Create fresh log with 23:00 default bedtime if missing
        last_log = DailyLog.query.filter_by(user_id=user.id).order_by(DailyLog.id.desc()).first()
        tb = getattr(last_log, 'target_bedtime', '23:00') if last_log else '23:00'
        
        log = DailyLog(
            user_id=user.id,
            date=today,
            target_bedtime=tb,
            app_usage_json=json.dumps(formatted_apps),
            academic_minutes_after_bedtime=0,
            pickups_after_bedtime=0
        )
        db.session.add(log)
    else:
        log.app_usage_json = json.dumps(formatted_apps)
        
    db.session.commit() # Flush so risk engine has updated variables
    
    # Recalculate AI Risk
    previous_logs = DailyLog.query.filter_by(user_id=user.id).order_by(DailyLog.date.desc()).limit(14).all()
    risk_score = RiskEngine.calculate_risk_score(log, previous_logs)
    log.risk_score = risk_score
    log.risk_level = RiskEngine.get_risk_level(risk_score)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'tracked_apps_count': len(formatted_apps),
        'risk_score': risk_score,
        'risk_level': log.risk_level
    }), 200

@main.route('/api/v1/morning_report', methods=['POST'])
@jwt_required()
def morning_report():
    user_id = get_jwt_identity()
    data = request.json
    
    latest_log = DailyLog.query.filter_by(user_id=user_id).order_by(DailyLog.id.desc()).first()
    if not latest_log:
        return jsonify({'error': 'No telemetry data to attach to'}), 404
        
    # User Inputs from Flutter
    time_to_asleep = int(data.get('time_to_fall_asleep_mins', 0))
    groggy_score = int(data.get('morning_grogginess_score', 1))
    
    feedback = InterventionFeedback.query.filter_by(daily_log_id=latest_log.id).first()
    if not feedback:
        feedback = InterventionFeedback(
            daily_log_id=latest_log.id,
            time_to_fall_asleep_mins=time_to_asleep,
            morning_grogginess_score=groggy_score,
            intervention_type='standard'
        )
        db.session.add(feedback)
    else:
        feedback.time_to_fall_asleep_mins = time_to_asleep
        feedback.morning_grogginess_score = groggy_score
        
    db.session.commit()
    
    # Generate Insight from Google Gemini Engine
    morning_summary = InsightEngine.generate_morning_report(latest_log, time_to_asleep)
    root_cause = InsightEngine.generate_root_cause_analysis(latest_log, time_to_asleep)
    
    return jsonify({
        "status": "success",
        "reinforcement": morning_summary['reinforcement'],
        "analysis": root_cause,
        "action_plan": morning_summary['action_plan']
    }), 200

@main.route('/api/v1/dashboard', methods=['GET'])
@jwt_required()
def dashboard_data():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    logs = DailyLog.query.filter_by(user_id=user_id).order_by(DailyLog.id.desc()).limit(7).all()
    stability_index = RiskEngine.calculate_stability_index(logs)
    
    latest = logs[0] if logs else None
    needs_checkin = False
    
    if latest:
        feedback = InterventionFeedback.query.filter_by(daily_log_id=latest.id).first()
        if not feedback:
            needs_checkin = True
            
    # Chart Data (reverse so oldest point is on the left)
    logs_for_chart = list(reversed(logs))
    
    return jsonify({
        'username': user.username,
        'stability_index': stability_index,
        'needs_morning_checkin': needs_checkin,
        'latest_risk_score': round(latest.risk_score, 2) if latest and latest.risk_score else 0,
        'latest_risk_level': latest.risk_level if latest else 'Unknown',
        'chart_labels': [log.date.strftime('%Y-%m-%d') for log in logs_for_chart],
        'chart_risk_data': [log.risk_score or 0 for log in logs_for_chart],
        'apps_usage': json.loads(latest.app_usage_json) if latest and latest.app_usage_json else [],
    }), 200
