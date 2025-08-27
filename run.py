# ==== AURA_V2/run.py ====
from app import create_app, db
from app.models import User, Client, DataSource
import os

config_name = os.getenv('FLASK_CONFIG') or 'default'
app = create_app(config_name)

@app.shell_context_processor
def make_shell_context():
    """Facilita o debug no terminal com 'flask shell'."""
    return {'db': db, 'User': User, 'Client': Client, 'DataSource': DataSource}

if __name__ == '__main__':
    app.run(debug=True)