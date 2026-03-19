import statistics

class RiskEngine:
    # Thresholds
    MAX_SOCIAL_HOURS = 5.0  # Increased to prevent saturation (was 2.0)
    MAX_ACADEMIC_HOURS = 5.0 # Increased (was 3.0)
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
        
        
        # 1. Social Impact (0.0 - 1.0)
        # Aggregate all platform usage
        total_social = (current_log.tiktok_ig_hours + 
                       current_log.youtube_hours + 
                       current_log.other_socials_hours + 
                       current_log.gaming_hours)
        
        social_score = min(total_social / RiskEngine.MAX_SOCIAL_HOURS, 1.0)
        
        # 2. Academic Impact (0.0 - 1.0)
        academic_score = min(current_log.academic_hours_after_bedtime / RiskEngine.MAX_ACADEMIC_HOURS, 1.0)
        
        # 3. Fragmentation (0.0 - 1.0)
        fragmentation_score = min(current_log.pickups_after_bedtime / RiskEngine.MAX_PICKUPS, 1.0)
        
        # 4. Consistency (Sleep Deviation)
        consistency_score = 0.0
        if len(previous_logs) > 1:
             # Calculate total late hours for today
             current_late = total_social + current_log.academic_hours_after_bedtime
             
             prev_late = []
             for log in previous_logs:
                 # Helper to safely sum social hours if they exist (backward compatibility or new model)
                 # Assuming migration or fresh DB, so new model fields apply.
                 # Optimistically assuming fresh start for prototype.
                 p_social = (getattr(log, 'tiktok_ig_hours', 0) + 
                             getattr(log, 'youtube_hours', 0) + 
                             getattr(log, 'other_socials_hours', 0) + 
                             getattr(log, 'gaming_hours', 0))
                 
                 # Fallback for old 'social_hours_after_bedtime' if mix of records?
                 # Given we are refactoring, we'll assume new structure.
                 
                 prev_late.append(p_social + log.academic_hours_after_bedtime)
            
             if prev_late:
                 avg_late = statistics.mean(prev_late)
                 if current_late > (avg_late + 1.0):
                     consistency_score = 1.0
        
        # Weighted Sum
        # Increased Social Weight slightly due to high-dopamine nature of new platforms?
        # Keeping original weights for now.
        raw_score = (0.5 * social_score) + \
                    (0.2 * academic_score) + \
                    (0.2 * fragmentation_score) + \
                    (0.1 * consistency_score)
                    
        return round(raw_score * 100, 2)

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
        Calculates stability based on low variance in 'late hours'.
        """
        if not previous_logs:
            return 100.0
            
        late_hours = []
        for log in previous_logs:
            # Handle potential missing attributes if old logs exist (though we reset DB)
            p_social = ((getattr(log, 'tiktok_ig_hours', 0.0) or 0.0) + 
                        (getattr(log, 'youtube_hours', 0.0) or 0.0) + 
                        (getattr(log, 'other_socials_hours', 0.0) or 0.0) + 
                        (getattr(log, 'gaming_hours', 0.0) or 0.0))
            late_hours.append(p_social + log.academic_hours_after_bedtime)
        
        if len(late_hours) < 2:
            return 100.0
            
        stdev = statistics.stdev(late_hours)
        # Normalize: Standard deviation. Reduced penalty factor to 20 (was 50).
        # SD of 1 hour = 80 Stability. SD of 5 hours = 0 Stability.
        stability = max(0, 100 - (stdev * 20))
        return round(stability, 2)
