import pandas as pd
from .. import db
from ..models import DailyLog, InterventionFeedback

class AnalyticsEngine:
    """
    Analyzes historical data to find mathematical correlations between 
    specific behaviors (Social, Academic, Pickups) and Sleep Latency / Grogginess.
    """

    @staticmethod
    def calculate_active_caffeine(caffeine_type, consumption_time, target_bedtime):
        """
        Calculates remaining active caffeine mg at bedtime using exponential decay.
        Formula: N(t) = N0 * (0.5) ^ (t / 5.5)
        """
        base_mg = {
            "Coffee": 95,
            "Tea": 47,
            "Energy Drink": 150,
            "Dark Chocolate": 12,
            "None": 0
        }
        
        n0 = base_mg.get(caffeine_type, 0)
        if n0 == 0 or not consumption_time or not target_bedtime:
            return 0.0
            
        try:
            from datetime import datetime
            time_format = "%H:%M"
            
            t_consume = datetime.strptime(consumption_time, time_format)
            t_bed = datetime.strptime(target_bedtime, time_format)
            
            # Handle cross-midnight logic if necessary (simplified for now)
            delta = t_bed - t_consume
            hours_elapsed = delta.total_seconds() / 3600.0
            
            # If they had coffee after bedtime, assume 0 decay for simplicity, or handle it properly 
            if hours_elapsed < 0:
                hours_elapsed += 24.0 # It was consumed the previous day...
                
            # N(t) = N0 * (0.5) ^ (t/5.5)
            active_mg = n0 * (0.5 ** (hours_elapsed / 5.5))
            return round(active_mg, 2)
            
        except Exception as e:
            print(f"Error calculating caffeine decay: {e}")
            return 0.0

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
            data.append({
                "tiktok_hours": log.tiktok_ig_hours,
                "youtube_hours": log.youtube_hours,
                "other_socials_hours": log.other_socials_hours,
                "gaming_hours": log.gaming_hours,
                "academic_hours": log.academic_hours_after_bedtime,
                "pickups": log.pickups_after_bedtime,
                "latency": feedback.time_to_fall_asleep_mins,
                "grogginess": feedback.morning_grogginess_score if feedback.morning_grogginess_score else 0
            })

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
            ("tiktok_hours", "TikTok/IG"),
            ("youtube_hours", "YouTube"),
            ("other_socials_hours", "Other Socials"),
            ("gaming_hours", "Gaming"),
            ("academic_hours", "Late Study"),
            ("pickups", "Phone Pickups")
        ]
        
        # Normalization Baselines (What counts as "Massive Usage" = 1.0)
        norm_limits = {
            "tiktok_hours": 2.0, "youtube_hours": 2.0, "other_socials_hours": 2.0, 
            "gaming_hours": 2.0, "academic_hours": 2.0, "pickups": 10.0
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
             
        if dimension == "tiktok_hours":
            if score > 0.4: return "High Dopamine Velocity: Short-form video is your #1 sleep killer."
            return "Moderate Impact: Dopamine looping is delaying onset."
            
        elif dimension == "youtube_hours":
             if score > 0.4: return "Parasocial Arousal: Long-form content is keeping you awake."
             return "Moderate Impact: Autoplay is likely the culprit."

        elif dimension == "other_socials_hours":
             if score > 0.4: return "Information Foraging: Your brain is hunting for novelty on social apps."
             return "Moderate Impact: Text consumption keeps the cortex active."

        elif dimension == "gaming_hours":
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


