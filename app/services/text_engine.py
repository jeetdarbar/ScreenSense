import random

class TextEngine:
    """
    The Voice of the System.
    Handles dynamic text generation using simplified, conversational, and educational language.
    Optimized for clarity and depth.
    """

    # --- NIGHTLY INSIGHT VOCABULARY ---
    # Simplified English, longer explanations, focus on "Why" and "How it feels"
    
    VOCAB_TIKTOK_IG = [
        "Short-form videos act like a slot machine for your brain. Every swipe offers a random chance of excitement, releasing quick bursts of dopamine. This 'variable reward' keeps you hooked and makes it incredibly hard to stop, leaving your brain buzzing when it needs to be quiet.",
        "Your brain needs a 'wind-down' period to prepare for sleep, but rapid scrolling keeps it in overdrive. By constantly switching contexts—from a funny clip to a sad one, then a dance—you prevent your mind from relaxing into the 'Default Mode Network', which is essential for drifting off.",
        "The bright, fast-moving visuals of scrolling tell your brain it's still daytime. This 'cognitive hyperarousal' suppresses melatonin, the hormone that makes you sleepy. Essentially, you are tricking your biology into staying awake, pushing your natural sleep time much later.",
        "You might be experiencing 'Dopamine Stacking'. This means your brain is hunting for the next hit of entertainment, making silence and boredom feel uncomfortable. To sleep well, you need to be okay with doing nothing for a few minutes."
    ]

    VOCAB_YOUTUBE = [
        "Autoplay is designed to dissolve your sense of time, a state known as 'Temporal Dissociation'. By removing the friction of choosing the next video, the algorithm keeps you in a passive trance. You might feel like only 10 minutes passed, when it's actually been an hour.",
        "Watching people talk or vlog triggers 'parasocial interaction'—your brain reacts as if you are actually socializing with them. This stimulates the social centers of your brain, keeping you alert and engaged exactly when you should be withdrawing from the world to rest.",
        "Binging videos puts you in a 'Passive Consumption State'. It feels relaxing, but it suppresses the natural sleep pressure signals your body sends. You might be physically tired, but your brain is being artificially propped up by the content.",
        "Long-form videos keep your visual cortex highly active. Even if the content is calm, the act of processing continuous visual data overrides your circadian drive, making it harder for your eyelids to feel heavy."
    ]

    VOCAB_REDDIT_X = [
        "You are engaged in 'Information Foraging'. Your primitive brain thinks it's hunting for valuable news or novelty, which keeps your survival instincts (the limbic system) active.",
        "Reading posts triggers 'Intellectual Arousal'. When you read an opinion you agree or disagree with, your prefrontal cortex lights up. This mental effort raises your core body temperature.",
        "The clear 'stopping points' between posts create a jagged rhythm of attention. You read, stop, process, then scroll again. This 'start-stop' cycle fragments your focus.",
        "Consuming dense information late at night increases your 'cognitive load'. Your brain has to work hard to process and store what you're reading."
    ]

    VOCAB_GAMING = [
        "Gaming triggers your 'Fight or Flight' response. The intense focus and need for quick reactions flood your system with adrenaline. This physical stress response is the exact opposite of what you need for sleep, which requires your heart rate to slow down.",
        "The intense concentration required for gaming releases norepinephrine, a chemical that physically blocks the 'sleepy molecule' called adenosine. You are chemically overriding your feeling of tiredness, which is why you can feel wide awake even if you are exhausted.",
        "High-action gameplay keeps your core body temperature elevated. For sleep to happen, your body temp needs to drop by a few degrees. By gaming, you are keeping your metabolic fire burning too hot for the sleep process to start.",
        "You are likely in a state of 'Flow', where you are so absorbed in the game that you lose track of time and bodily sensations. In this state, your brain ignores biological signals like heavy eyes or distinct sleepiness until you stop playing."
    ]
    
    
    # --- MORNING ROOT CAUSE VOCABULARY ---
    # Structure: {Mechanism} -> {Impact}
    # Goal: Long, educational, simple English.
    
    RC_MECHANISMS = {
        "Social Media": [
            "The endless scroll created a loop of 'hyper-stimulation',",
            "The rapid visual cuts and bright colors of social feeds",
            "Getting continuous small hits of dopamine from scrolling"
        ],
        "Game": [
            "The rush of adrenaline from playing an interactive game",
            "The high-intensity focus you needed to play",
            "The competitive and fast-paced nature of the game"
        ],
        "Other": [
            "Hunting for new information and reading updates",
            "The mental effort required to process the screen",
            "The stop-and-start rhythm of checking apps"
        ]
    }
    
    RC_IMPACTS = {
        "Delayed": [ # 30-60 mins
            "kept your stress hormones slightly elevated. This acts like a mild caffeine hit, directly delaying the moment you could fall asleep.",
            "prevented your brain from settling into the relaxed 'alpha-wave' state. You need this calm state to drift off, so you stayed awake longer.",
            "pushed your internal clock backward. It tricked your brain into thinking it was earlier than it was, making 11 PM feel like 9 PM.",
            "created a 'Tired but Wired' feeling. Your body was exhausted, but your mind was still racing, unable to shut down."
        ],
        "Severe": [ # > 60 mins
            "caused a state of 'Cognitive Hyperarousal'. This means your brain was so active processing stimuli that it completely blocked the transition into light sleep.",
            "triggered a 'Second Wind'. You pushed past your natural sleep window, and your body released energy to keep you awake, overriding your tiredness entirely.",
            "kept your body temperature too high. Your body needs to cool down to sleep, but the mental activity kept your metabolism running fast.",
            "hijacked your brain's reward system. Compared to the high-stimulation of the screen, sleep felt chemically 'boring' to your brain, so it resisted shutting down."
        ]
    }

    @staticmethod
    def generate_nightly_insight(apps):
        """
        Returns a detailed, simplified explanation based on the primary platform driver.
        """
        if not apps:
             return "Your digital footprint is minimal. This is great! Your circadian rhythm (body clock) is protected from the interference of algorithms, allowing you to sleep naturally."

        highest_app = max(apps, key=lambda a: a.get('minutes', 0))
        driver_name = highest_app.get('name', 'Unknown')
        category = highest_app.get('category', 'Other')
        max_val = highest_app.get('minutes', 0)
        
        if max_val < 15:
             return "Your digital footprint is minimal. This is great! Your circadian rhythm (body clock) is protected from the interference of algorithms, allowing you to sleep naturally."

        if category == "Social Media": 
            return f"Because you used {driver_name}: " + random.choice(TextEngine.VOCAB_TIKTOK_IG)
        elif category == "Game": 
            return f"Playing {driver_name}: " + random.choice(TextEngine.VOCAB_GAMING)
            
        return f"Digital consumption via {driver_name} detected. Monitor your screen time to protect sleep quality."

    @staticmethod
    def generate_morning_analysis(apps, minutes_to_sleep, grogginess_score=1):
        """
        Generates a detailed, non-repetitive Root Cause Analysis in simple English.
        """
        if not apps:
            return "No massive screen usage detected! Your circadian sync is perfect."
            
        highest_app = max(apps, key=lambda a: a.get('minutes', 0))
        driver = highest_app.get('name', 'your phone')
        category = highest_app.get('category', 'Other')
        max_val = highest_app.get('minutes', 0)
        total_usage = sum(app.get('minutes', 0) for app in apps)
        
        # 2. Multi-Factor "Overload" Detection
        if total_usage > 180:
            return (f"⚠️ DOPAMINE BURNOUT: You spent a total of {total_usage} minutes on screens. "
                    f"This creates a huge 'Stimulation Debt' for your brain. "
                    f"Even if you felt physically tired, your mind was chemically too loud and active to sleep peacefully. "
                    f"It's like trying to park a car that's moving at 100 miles per hour.")

        # Phase 4: 3. Sleep Inertia (Grogginess) Correlation Check
        if grogginess_score >= 7 and max_val > 60 and minutes_to_sleep < 30:
            return (f"🧠 ARCHITECTURE COLLAPSE: Interestingly, {driver} didn't delay your sleep onset much ({minutes_to_sleep}m), "
                    f"but it has a massive correlation with your severe morning brain fog (Score: {grogginess_score}/10). "
                    f"This indicates your deep REM sleep architecture was compromised by screen glare, giving you 'junk sleep'.")

        # 4. Crash Detection (Fast Sleep + High Usage)
        if minutes_to_sleep < 15 and max_val > 90:
             return (f"⚠️ EXHAUSTION MASK: You fell asleep very quickly ({minutes_to_sleep}m), but this isn't necessarily healthy. "
                     f"Using {driver} for {max_val}m likely caused you to 'crash' from exhaustion rather than drift off naturally. "
                     f"This leads to 'Sleep Inertia', where you wake up feeling groggy because your sleep quality was poor.")
                     
        # 5. Validation (Low Usage + Fast Sleep + Low Grogginess)
        if max_val < 30 and minutes_to_sleep < 20 and grogginess_score <= 3:
            return (f"✅ CIRCADIAN SYNC: Because you had minimal interference from {driver}, your natural 'sleep pressure' worked correctly. "
                    f"Falling asleep in {minutes_to_sleep}m with high morning alertness is a great sign that your routine is perfectly synced.")

        # 6. Latency Analysis (The Core Logic)
        mechanism = random.choice(TextEngine.RC_MECHANISMS.get(category, ["using screens"]))
        
        if minutes_to_sleep > 60:
            impact = random.choice(TextEngine.RC_IMPACTS["Severe"])
            prefix = "🛑 SEVERE DISRUPTION: "
        elif minutes_to_sleep > 30:
            impact = random.choice(TextEngine.RC_IMPACTS["Delayed"])
            prefix = "⚠️ DELAYED ONSET: "
        else:
            # Fallback for moderate usage + normal sleep (15-30m)
            return (f"⚖️ BALANCED: Your usage of {driver} ({max_val}m) was tolerated well by your body tonight. "
                    f"Your sleep onset of {minutes_to_sleep}m is normal. However, be careful, as you are at the limit. "
                    f"If you wake up feeling groggy, try cutting back slightly tomorrow.")

        return f"{prefix}{mechanism} ({max_val}m) {impact}"

