import pandas as pd
from .. import db
from ..models import DailyLog, InterventionFeedback

class AnalyticsEngine:
    """
    Analyzes historical data to find mathematical correlations between 
    specific behaviors (Social, Academic, Pickups) and Sleep Latency / Grogginess.
    """

    @staticmethod
    def calculate_behavioral_correlations(user_id, limit=10):
        """
        Fetches last `limit` entries (default 10), calculates Pearson correlation,
        and returns actionable insights.
        """
        # 1. Fetch Data joined with Feedback
        # We need logs that HAVE feedback to calculate correlation with latency
        results = db.session.query(DailyLog, InterventionFeedback).\
            join(InterventionFeedback, DailyLog.id == InterventionFeedback.daily_log_id).\
            filter(DailyLog.user_id == user_id).\
            order_by(DailyLog.date.desc()).\
            limit(limit).\
            all()

        if len(results) < 3:
            return {
                "error": "Insufficient data. Need at least 3 nights of Morning Check-Ins to calculate correlations."
            }

        # 2. Extract Data into List of Dicts
        data = []
        for log, feedback in results:
            row = {
                "academic_hours": log.academic_minutes_after_bedtime / 60.0,
                "pickups": log.pickups_after_bedtime,
                "latency": feedback.time_to_fall_asleep_mins,
                "grogginess": feedback.morning_grogginess_score if feedback.morning_grogginess_score else 0
            }
            # Dynamically flatten app categories for pie chart
            for app in log.get_usage_list():
                cat = app.get('category')
                key = cat.lower().replace(' ', '_') + "_hours" if cat else "other"
                row[key] = row.get(key, 0) + (app.get('minutes', 0) / 60.0)
                
            data.append(row)

        # 3. Create DataFrame
        df = pd.DataFrame(data)

        # 4. Calculate Correlation Matrix (Pearson)
        # We only care about correlation with 'latency' and 'grogginess'
        # fillna(0) to handle cases where std dev is 0 (e.g. constant values)
        correlations_latency = df.corr(method='pearson')['latency'].fillna(0)
        correlations_grogginess = df.corr(method='pearson')['grogginess'].fillna(0)

        # 5. Extract & Interpret Scores (Impact Score)
        analysis = {}
        
        # Dimensions to analyze
        dimensions = [
            ("social_media_hours", "Social Media"),
            ("game_hours", "Gaming"),
            ("academic_hours", "Late Study"),
            ("pickups", "Phone Pickups")
        ]
        
        # Normalization Baselines (What counts as "Massive Usage" = 1.0)
        norm_limits = {
            "social_media_hours": 2.0, "game_hours": 2.0, "academic_hours": 2.0, "pickups": 10.0
        }

        for col, label in dimensions:
            r_lat = correlations_latency.get(col, 0)
            r_grog = correlations_grogginess.get(col, 0)
            
            avg_usage = df[col].mean()
            limit = norm_limits.get(col, 2.0)
            
            # Usage Weight (0.0 to 1.0)
            w = min(avg_usage / limit, 1.0)
            
            # Impact Score Formula: Bound mathematical correlation by actual usage volume
            # so low-usage items don't trigger false positives.
            if r_lat > 0:
                impact_score = w + (r_lat * w)
            else:
                # Negative correlations slightly reduce the apparent risk, but don't erase high volume
                impact_score = w + (r_lat * 0.3)
            
            final_score = round(max(0.0, impact_score), 2)
            insight = AnalyticsEngine._generate_insight(col, final_score, r_grog)
            
            analysis[col] = {
                "label": label,
                "score": final_score,
                "insight": insight,
                "raw_r_latency": round(r_lat, 2), # Debug info
                "raw_r_grogginess": round(r_grog, 2),
                "avg_usage": round(avg_usage, 1)
            }

        return analysis

    @staticmethod
    def _generate_insight(dimension, score, r_grog):
        """
        Returns a hardcoded string insight based on the raw correlation score and grogginess.
        """
        # Positive correlation = Higher Usage leads to Higher Latency (BAD)
        
        # Phase 4 addition: Check Grogginess first if latency isn't the main issue
        if score <= 0.2 and r_grog > 0.6:
            return "Destroys REM sleep architecture, causing severe morning brain fog without affecting onset."
            
        if score <= 0.05:
             return "No Negative Correlation: Not currently affecting latency."
             
        if dimension == "social_media_hours":
            if score > 0.4: return "High Dopamine Velocity: Social media is your #1 sleep killer."
            return "Moderate Impact: Dopamine looping is delaying onset."

        elif dimension == "game_hours":
             if score > 0.4: return "Adrenaline Spike: Competitive play is physically blocking sleep."
             return "Moderate Impact: Cool down required before bed."

        elif dimension == "academic_hours":
            if score > 0.5:
                return "Critical: Late night studying is keeping your brain too alert."
            elif score > 0.2:
                return "Noticeable: Try to finish homework 1 hour earlier."
            else:
                return "Low Impact: Late studying is currently not a major disruptor for you."

        elif dimension == "pickups":
            if score > 0.5:
                return "High Disruption: Every unlock is resetting your sleep timer."
            elif score > 0.2:
                return "Moderate: Try putting your phone across the room."
            else:
                return "Stable: Your pickup habits are not significantly delaying sleep."

        return "Data analysis complete."


