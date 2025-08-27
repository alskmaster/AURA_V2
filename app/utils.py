# ==== AURA_V2/app/utils.py ====

from functools import wraps
from flask import abort
from flask_login import current_user

def admin_required(f):
    """
    Decorador que garante que o utilizador atual está autenticado e
    tem o papel 'Admin'. Se não, retorna um erro 403 (Proibido).
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_role('Admin'):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function