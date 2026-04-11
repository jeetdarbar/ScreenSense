import statistics

class RiskEngine:
    # Thresholds
    MAX_SOCIAL_MINUTES = 300.0  # Increased to prevent saturation (was 5.0 hours)
    MAX_ACADEMIC_MINUTES = 300.0 # Increased (was 5.0 hours)
    MAX_PICKUPS = 15        # Increased (was 10)
    
    @staticmethod
    def calculate_risk_score(current_log, previous_logs):
        """
        Calculates Risk Score based on Social vs Academic usage after bedtime.
        
        Weights:
        - Social Media After Bedtime: 50% (High impact on dopamine/sleep)
        - Academic Work After Bedtime: 20% (Stress impact)
        - Pickups After Bedtime: 20% (Fragmentation)
        - Consistency (Deviation): 10%
        """
        
        # 1. Dynamic Categorical Impact
        risk_score = 20.0 # Base risk
        
        total_social_minutes = 0
        total_gaming_minutes = 0
        
        for app in current_log.get_usage_list():
            cat = app.get('category', 'Other')
            mins = app.get('minutes', 0)
            
            if cat == 'Social Media':
                risk_score += (mins / 60.0) * 15.0  # 15 risk chunks per hour
                total_social_minutes += mins
            elif cat == 'Game':
                risk_score += (mins / 60.0) * 12.0  # 12 risk chunks per hour
                total_gaming_minutes += mins
                
        # 2. Academic Impact
        risk_score += (min(current_log.academic_minutes_after_bedtime / RiskEngine.MAX_ACADEMIC_MINUTES, 1.0)) * 10.0
        
        # 3. Fragmentation
        risk_score += (min(current_log.pickups_after_bedtime / RiskEngine.MAX_PICKUPS, 1.0)) * 20.0
        
        # 4. Consistency (Sleep Deviation)
        consistency_penalty = 0.0
        if len(previous_logs) > 1:
             current_late = total_social_minutes + total_gaming_minutes + current_log.academic_minutes_after_bedtime
             
             prev_late = []
             for log in previous_logs:
                 p_social = 0
                 # Support dynamically scanning historical logs too!
                 for p_app in log.get_usage_list():
                     if p_app.get('category') in ['Social Media', 'Game']:
                         p_social += p_app.get('minutes', 0)
                 prev_late.append(p_social + getattr(log, 'academic_minutes_after_bedtime', 0))
            
             if prev_late:
                 avg_late = statistics.mean(prev_late)
                 if current_late > (avg_late + 60.0): # 60 minutes deviation
                     consistency_penalty = 10.0
                     
        risk_score += consistency_penalty
        
        # Cap at 100
        return round(min(risk_score, 100.0), 2)

    @staticmethod
    def get_risk_level(score):
        if score <= 40:
            return "Safe"
        elif score <= 70:
            return "Moderate"
        else:
            return "High"

    @staticmethod
    def calculate_stability_index(previous_logs):
        """
        Calculates stability based on low variance in 'late minutes'.
        """
        if not previous_logs:
            return 100.0
            
        late_minutes = []
        for log in previous_logs:
            p_social = 0
            for app in log.get_usage_list():
                if app.get('category') in ['Social Media', 'Game']:
                    p_social += app.get('minutes', 0)
            late_minutes.append(p_social + getattr(log, 'academic_minutes_after_bedtime', 0))
        
        if len(late_minutes) < 2:
            return 100.0
            
        stdev = statistics.stdev(late_minutes)
        # Normalize: Standard deviation. 
        # SD of 60 minutes = 80 Stability. 
        stability = max(0, 100 - (stdev * (20.0/60.0)))
        return round(stability, 2)
