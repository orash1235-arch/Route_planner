from app import create_app
from flaskwebgui import FlaskUI

app = create_app()

if __name__ == "__main__":
    # Controls Flask lifecycle and opens a dedicated window
    FlaskUI(app=app, server="flask", width=1200, height=800).run()