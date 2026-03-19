from app import create_app, db

app = create_app()

with app.app_context():
    try:
        db.drop_all()
        db.create_all()
        print("Database schema dropped and recreated successfully with new columns.")
    except Exception as e:
        print(f"Error resetting schema: {e}")
