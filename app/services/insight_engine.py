import random

class InsightEngine:
    """
    Generates personalized, scientifically grounded feedback based on sleep behavior.
    """

    @staticmethod
    def generate_nightly_insight(log_data):
        """
        Analyzes the evening check-in data and returns actionable insights.
        Now delegates text generation to the dynamic TextEngine.
        """
        from app.services.text_engine import TextEngine
        
        apps = log_data.get_usage_list()
        
        # Get dynamic scientific explanation from TextEngine
        impact_msg = TextEngine.generate_nightly_insight(apps)
        
        # Keep action logic simple here, or move to TextEngine later if needed.
        # For now, just randomization or static advice based on the driver.
        action_msg = "Focus on a consistent wind-down routine."
        
        total_social = sum(app.get('minutes', 0) for app in apps if app.get('category') == 'Social Media')
        academic = log_data.academic_minutes_after_bedtime
        pickups = log_data.pickups_after_bedtime
        
        if total_social > 60:
            action_msg = "Try 'bundling' leisure time earlier or use Grayscale Mode."
        elif academic > 90:
             action_msg = "Write a to-do list for tomorrow to offload cognitive tasks."
        elif pickups > 5:
             action_msg = "Turn on 'Do Not Disturb' or place phone face down."
             
        return {
            "why_impact": impact_msg,
            "how_action": action_msg
        }

    @staticmethod
    def generate_morning_report(log_data, minutes_to_sleep):
        """
        Generates morning reinforcement and a dynamic action plan based on sleep onset latency and grogginess.
        """
        # Aggregate social for simplified reinforcement logic
        total_social = sum(app.get('minutes', 0) for app in log_data.get_usage_list() if app.get('category') == 'Social Media')

        # Phase 4 Extract Grogginess (if passed, else default)
        # Note: routes.py passes minutes_to_sleep, we'll try to extract grogginess if available
        # or just rely on latency for the main routing.
        grogginess = getattr(log_data, 'morning_grogginess_score', 1) 
        
        # 1. Reinforcement (Positive Reinforcement)
        reinforcement = ""
        if total_social < 30:
             reinforcement = "Excellent control over social media reward loops last night."
        elif getattr(log_data, 'academic_minutes_after_bedtime', 0) < 30:
             reinforcement = "Great job managing cognitive load before bed."
        elif getattr(log_data, 'pickups_after_bedtime', 0) < 3:
             reinforcement = "Minimal sleep fragmentation detected. Good discipline."
        else:
             reinforcement = "Thank you for logging your data. Awareness is the first step."

        # 2. Dynamic Action Plan (Mitigation)
        # Pools of advice to keep the report fresh daily
        disrupted_pool = [
            "Get 15 mins of AM sunlight viewing immediately to reset circadian rhythm.",
            "Implement a strict caffeine cutoff by 1 PM to let adenosine clear out.",
            "Shift tonight's wind-down protocol 20 minutes earlier than usual.",
            "Try 10 minutes of NSDR (Non-Sleep Deep Rest) this afternoon to recover.",
            "Lower the thermostat tonight—a cold room triggers faster sleep onset.",
            "Avoid heavy meals within 3 hours of your target bedtime.",
            "Leave your phone in another room tonight to break the pickup habit."
        ]
        
        stable_pool = [
            "Maintain your current circadian inputs—your routine is working.",
            "Hydrate with 16oz of water within 30 minutes of waking.",
            "Delay caffeine for 90 minutes after waking to avoid the afternoon crash.",
            "Keep your bedtime consistent tonight to lock in this momentum.",
            "Consider a 5-minute morning walk to further solidify your circadian anchor."
        ]

        # Determine condition (Latency > 30 mins OR high grogginess)
        if minutes_to_sleep > 30 or grogginess >= 5:
            # Select 3 random pieces of advice from the disrupted pool
            action_plan = random.sample(disrupted_pool, 3)
        else:
            # Select 2-3 random pieces from the stable pool
            action_plan = random.sample(stable_pool, 3)

        return {
            "reinforcement": reinforcement,
            "action_plan": action_plan
        }

    @staticmethod
    def generate_root_cause_analysis(daily_log, time_to_sleep_mins, grogginess_score=1):
        """
        Deep dive analysis connecting usage behaviors to the reported sleep latency and grogginess.
        Used for the Morning Report.
        """
        from app.services.text_engine import TextEngine

        # Phase 4 Updates: Grab caffeine data from the log
        caffeine_mg = getattr(daily_log, 'active_caffeine_mg', 0.0)
        caffeine_modifiers = getattr(daily_log, 'caffeine_modifiers', False)
        
        # We also need to extract specifically which app was the problem, TextEngine handles this.
        return TextEngine.generate_morning_analysis(
            daily_log.get_usage_list(),
            time_to_sleep_mins,
            caffeine_mg,
            caffeine_modifiers,
            grogginess_score
        )

    # Phase 5: Dynamic Audio Prescription
    @staticmethod
    def get_audio_prescription(daily_log):
        """
        Determines the optimal acoustic intervention for the Wind-Down Portal based on
        the highest risk usage behavior for the current night.
        Returns a dictionary with primary track info and alternative tracks.
        """
        usage = {
            "Academic/Work": getattr(daily_log, 'academic_minutes_after_bedtime', 0),
        }
        
        # Dynamically push highest apps
        for app in daily_log.get_usage_list():
            if app.get('minutes', 0) > usage.get(app.get('name'), 0):
                usage[app.get('name')] = app.get('minutes', 0)
        
        # Determine highest driver
        highest_driver = max(usage, key=usage.get)
        max_val = usage[highest_driver]
        
        # Audio library mappings
        tracks = [
            {"id": "binaural", "url": "/static/audio/binaural_delta.wav", "name": "Deep Delta (3Hz)", "desc": "Binaural beats to flush Cortisol."},
            {"id": "brown_noise", "url": "/static/audio/brown_noise.wav", "name": "Brown Noise", "desc": "Low-frequency rumble for general relaxation."},
            {"id": "rhythm_60", "url": "/static/audio/rhythm_60bpm.wav", "name": "Acoustic 60 BPM", "desc": "Synchronizes heart rate to resting pace."},
            {"id": "nature", "url": "/static/audio/nature_ambient.wav", "name": "Ambient Nature", "desc": "Pink noise waves to lower Dopamine."}
        ]
        
        def get_track(track_id):
            return next((t for t in tracks if t['id'] == track_id), tracks[0])
            
        # Default baseline if no severe usage
        primary = get_track("brown_noise")
        reasoning = "Just a light ambient noise to help you transition into sleep."
        
        if max_val >= 30:
            if highest_driver == "Academic/Work":
                primary = get_track("binaural")
                reasoning = "High Academic/Work hours detected. We prescribed Binaural Delta waves to help clear cortisol and physically slow your brainwaves down."
            else:
                primary = get_track("nature")
                reasoning = f"Extended {highest_driver} usage spiked your dopamine levels. Ambient Nature sounds provide soothing, unpredictable pink noise to calm the chemical noise in your brain."

        audio_payload = {
            "primary_track": primary,
            "reasoning": reasoning,
            "all_tracks": tracks
        }
        
        return audio_payload
