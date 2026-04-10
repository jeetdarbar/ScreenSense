from app import create_app
from flask import request, jsonify

app = create_app()

@app.route('/api/sync_usage', methods=['POST'])
def sync_usage():
    data = request.get_json()
    stats = data.get('stats', [])

    social_mins = 0
    game_mins = 0

    # Categorize the data for your ML model
    for app in stats:
        if app['category'] == 'Social Media':
            social_mins += app['minutes']
        elif app['category'] == 'Game':
            game_mins += app['minutes']

    # This prints to your Render Logs so you can see it working!
    print(f"DEBUG: Social: {social_mins}m, Games: {game_mins}m")

    # TODO: Pass these variables into your Random Forest model
    # prediction = my_model.predict([[social_mins, game_mins]])

    return jsonify({
        "status": "success",
        "social": social_mins,
        "games": game_mins
    })