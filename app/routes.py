from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from . import db
from .models import User, DailyLog, InterventionFeedback
from .services.risk_engine import RiskEngine
from .services.insight_engine import InsightEngine
from datetime import datetime, timedelta

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('splash.html', is_auth=current_user.is_authenticated)

@main.route('/login-page', endpoint='login_page')
def login_page_view():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('auth.html')

@main.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password):
        login_user(user, remember=True)
        return jsonify({'message': 'Logged in successfully'}), 200
        
    return jsonify({'error': 'Invalid email or password'}), 401

@main.route('/register', methods=['POST'])
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
    
    login_user(new_user, remember=True)
    return jsonify({'message': 'Registration successful'}), 201

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@main.route('/dashboard')
@login_required
def dashboard():
    user = current_user
        
    # Check for Morning Check-In State
    # Logic: If latest log exists AND has no feedback -> Needs Morning Check-In
    # Order by ID to ensure we get the absolute latest submission (even if same date)
    latest_log = DailyLog.query.filter_by(user_id=user.id).order_by(DailyLog.id.desc()).first()
    
    needs_morning_checkin = False
    if latest_log:
        # Check if feedback exists
        feedback = InterventionFeedback.query.filter_by(daily_log_id=latest_log.id).first()
        if not feedback:
            needs_morning_checkin = True

    log_count = DailyLog.query.filter_by(user_id=user.id).count()
            
    return render_template('dashboard.html', needs_morning_checkin=needs_morning_checkin, log_count=log_count, latest_log=latest_log)

@main.route('/checkin', methods=['POST'])
@login_required
def checkin():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No JSON payload received'}), 400
            
        user_id = current_user.id
        
        # Parse new inputs
        try:
            target_bedtime = data.get('target_bedtime', "23:00")
            
            # Platform Breakdown
            tiktok_ig_minutes = int(data.get('tiktok_ig_minutes', 0))
            youtube_minutes = int(data.get('youtube_minutes', 0))
            other_socials_minutes = int(data.get('other_socials_minutes', 0))
            gaming_minutes = int(data.get('gaming_minutes', 0))
            
            academic_minutes = int(data.get('academic_minutes_after_bedtime', 0))
            pickups = int(data.get('pickups_after_bedtime', 0))
            
            # Phase 4: Caffeine
            from .services.analytics import AnalyticsEngine
            caffeine_type = data.get('caffeine_type', "None")
            caffeine_time = data.get('caffeine_time', None)
            caffeine_modifiers = bool(data.get('caffeine_modifiers', False))
            
            active_caffeine_mg = AnalyticsEngine.calculate_active_caffeine(caffeine_type, caffeine_time, target_bedtime)
            
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid input data'}), 400

        new_log = DailyLog(
            user_id=user_id,
            date=datetime.utcnow().date(),
            target_bedtime=target_bedtime,
            
            academic_minutes_after_bedtime=academic_minutes,
            pickups_after_bedtime=pickups,
            
            caffeine_type=caffeine_type,
            caffeine_time=caffeine_time,
            caffeine_modifiers=caffeine_modifiers,
            active_caffeine_mg=active_caffeine_mg
        )
        
        # Fetch previous logs for trends
        previous_logs = DailyLog.query.filter_by(user_id=user_id).order_by(DailyLog.date.desc()).limit(14).all()
        
        # Calculate Risk (Enabled)
        risk_score = RiskEngine.calculate_risk_score(new_log, previous_logs)
        risk_level = RiskEngine.get_risk_level(risk_score)
        
        # Save to DB
        new_log.risk_score = risk_score
        new_log.risk_level = risk_level
        
        db.session.add(new_log)
        db.session.commit()
        
        # Generate Insight
        insight = InsightEngine.generate_nightly_insight(new_log)
        
        return jsonify({
            'message': 'Check-in saved',
            'risk_score': round(new_log.risk_score, 2),
            'risk_level': new_log.risk_level,
            'insight': insight,
            'audio_prescription': InsightEngine.get_audio_prescription(new_log) # Phase 5
        }), 201
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@main.route('/dashboard-data', methods=['GET'])
@login_required
def get_dashboard_data():
    user_id = current_user.id
    
    # Get last 7 entries (ordered by ID to ensure latest submission is first, even on same day)
    logs = DailyLog.query.filter_by(user_id=user_id).order_by(DailyLog.id.desc()).limit(7).all()
    
    # Calculate Stability based on recent logs usage pattern
    stability_index = RiskEngine.calculate_stability_index(logs)
    
    # Reverse for chart display (oldest to newest for x-axis)
    logs_for_chart = list(reversed(logs))
    
    chart_labels = [log.date.strftime('%Y-%m-%d') for log in logs_for_chart]
    chart_risk_data = [log.risk_score if log.risk_score is not None else 0 for log in logs_for_chart]
    
    return jsonify({
        'stability_index': stability_index,
        'chart_labels': chart_labels,
        'chart_risk_data': chart_risk_data,
        'latest_risk_level': logs[0].risk_level if logs else 'Safe',  # logs[0] is now the NEWEST
        'latest_risk_score': round(logs[0].risk_score, 2) if logs and logs[0].risk_score is not None else 0,
        'audio_prescription': InsightEngine.get_audio_prescription(logs[0]) if logs else None
    })

@main.route('/api/morning_feedback', methods=['POST'])
@login_required
def morning_feedback():
    data = request.json
    user_id = current_user.id
    # Get the log from the PREVIOUS night (or just the latest log)
    # Use ID to match the logic in index route
    latest_log = DailyLog.query.filter_by(user_id=user_id).order_by(DailyLog.id.desc()).first()
    
    if not latest_log:
        return jsonify({'error': 'No log found to attach feedback to'}), 404
        
    try:
        minutes = int(data.get('time_to_fall_asleep_mins'))
        # Phase 4: Capture Morning Grogginess Score
        grogginess_score = int(data.get('morning_grogginess_score', 1))
    except (ValueError, TypeError):
         return jsonify({'error': 'Invalid input'}), 400
    
    # Update or Create InterventionFeedback
    feedback = InterventionFeedback.query.filter_by(daily_log_id=latest_log.id).first()
    if not feedback:
        feedback = InterventionFeedback(
            daily_log_id=latest_log.id,
            time_to_fall_asleep_mins=minutes,
            morning_grogginess_score=grogginess_score,
            intervention_type='standard' # default
        )
        db.session.add(feedback)
    else:
        feedback.time_to_fall_asleep_mins = minutes
        feedback.morning_grogginess_score = grogginess_score
    
    db.session.commit()
    
    # Logic to Generate Report
    # 1. Get Nightly Insight (Analysis)
    nightly_insight = InsightEngine.generate_nightly_insight(latest_log)
    
    # 2. Get Morning Report (Reinforcement + Action Plan)
    morning_report = InsightEngine.generate_morning_report(latest_log, minutes)
    
    # 3. Generate Specific Root Cause Analysis
    root_cause = InsightEngine.generate_root_cause_analysis(latest_log, minutes)
    
    # 4. Construct Final JSON
    response_data = {
        "reinforcement": morning_report['reinforcement'],
        "analysis": root_cause, # Use the new specific analysis
        "action_plan": morning_report['action_plan']
    }
    
    return jsonify(response_data)

@main.route('/api/analytics/correlations', methods=['GET'])
@login_required
def get_correlations():
    user_id = current_user.id
    from .services.analytics import AnalyticsEngine
    
    analysis = AnalyticsEngine.calculate_behavioral_correlations(user_id)
    return jsonify(analysis)

@main.route('/api/sync/usage', methods=['POST'])
def sync_usage():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({'error': 'Missing or invalid Authorization header'}), 401
    
    token = auth_header.split(" ")[1]
    user = User.query.filter_by(api_token=token).first()
    if not user:
        return jsonify({'error': 'Invalid API token'}), 401
        
    data = request.json
    if data is None:
        return jsonify({'error': 'No payload provided'}), 400
        
    try:
        today = datetime.utcnow().date()
        log = DailyLog.query.filter_by(user_id=user.id, date=today).first()
        
        # Extract precise minute telemetry
        # Data is now a JSON Array of individual apps
        import json
        app_list = data if isinstance(data, list) else []
        
        if not log:
            # First background sync of the night.
            last_log = DailyLog.query.filter_by(user_id=user.id).order_by(DailyLog.id.desc()).first()
            tb = getattr(last_log, 'target_bedtime', '23:00') if last_log else '23:00'
            
            log = DailyLog(
                user_id=user.id,
                date=today,
                target_bedtime=tb,
                app_usage_json=json.dumps(app_list),
                academic_minutes_after_bedtime=0,
                pickups_after_bedtime=0
            )
            db.session.add(log)
        else:
            # Update existing nightly log continuously
            log.app_usage_json = json.dumps(app_list)
            
        db.session.commit() # Flush so risk engine can query previous logs safely
        
        # Dynamically recalculate risk using surrounding database knowledge
        previous_logs = DailyLog.query.filter_by(user_id=user.id).order_by(DailyLog.date.desc()).limit(14).all()
        risk_score = RiskEngine.calculate_risk_score(log, previous_logs)
        log.risk_score = risk_score
        log.risk_level = RiskEngine.get_risk_level(risk_score)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Automated usage synced successfully.',
            'risk_score': round(risk_score, 2),
            'risk_level': log.risk_level
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
