# backend/auth.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from sqlalchemy import text as sql_text
from models import db, User

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _json_error(message: str, status_code: int):
    return jsonify(error=message, msg=message), status_code


def _json_message(message: str, status_code: int = 200):
    return jsonify(message=message, msg=message), status_code


def _sync_user_id_sequence_if_needed():
    """Sync PostgreSQL user ID sequence after manual creation of fixed internal user IDs."""
    engine_name = db.engine.url.get_backend_name()
    if not engine_name.startswith("postgresql"):
        return

    max_user_id = db.session.execute(sql_text('SELECT COALESCE(MAX(id), 0) FROM "user"')).scalar()
    sequence_name = db.session.execute(
        sql_text("SELECT pg_get_serial_sequence('\"user\"', 'id')")
    ).scalar()
    if not sequence_name:
        return

    if max_user_id and max_user_id > 0:
        db.session.execute(
            sql_text("SELECT setval(:sequence_name, :max_user_id, true)"),
            {"sequence_name": sequence_name, "max_user_id": int(max_user_id)},
        )
    else:
        db.session.execute(
            sql_text("SELECT setval(:sequence_name, 1, false)"),
            {"sequence_name": sequence_name},
        )


@auth_bp.post("/register")
def register():
    data = request.json or {}
    if not data.get("username") or not data.get("password"):
        return _json_error("用户名和密码不能为空", 400)
    if User.query.filter_by(username=data["username"]).first():
        return _json_error("用户已存在", 400)

    try:
        _sync_user_id_sequence_if_needed()
        u = User(username=data["username"])
        u.set_password(data["password"])
        db.session.add(u)
        db.session.commit()
        return _json_message("注册成功")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Error during registration for {data.get('username')}: {e}", exc_info=True
        )
        return _json_error("注册过程中发生错误", 500)


@auth_bp.post("/login")
def login():
    data = request.json or {}
    if not data.get("username") or not data.get("password"):
        return _json_error("需要提供用户名和密码", 400)

    u = User.query.filter_by(username=data["username"]).first()
    if not (u and u.check_password(data["password"])):
        return _json_error("用户名或密码错误", 401)

    try:
        # Store user ID as string in identity, consistent with loader
        token = create_access_token(identity=str(u.id))
        # Optionally update last login time
        u.last_login_at = db.func.now()
        db.session.commit()
        return jsonify(access_token=token)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Error during login for {data.get('username')}: {e}", exc_info=True
        )
        return _json_error("登录过程中发生错误", 500)


@auth_bp.get("/me")
@jwt_required()  # Handles token validity and user existence via loaders in app.py
def me():
    """Returns the current user's basic information."""
    uid_str = get_jwt_identity()  # Identity is guaranteed to be valid if we are here
    try:
        user_id = int(uid_str)
        user = User.query.get(user_id)
        # The user_lookup_loader in app.py already verified the user exists.
        # This get() is just to retrieve the object again within the request context.
        if user is None:
            # This case should technically be unreachable due to user_lookup_error_loader,
            # but added for robustness.
            current_app.logger.error(
                f"/me route: User lookup loader ok but User.query.get({user_id}) is None."
            )
            return _json_error("无法找到用户信息", 404)

        return jsonify(id=user.id, username=user.username)
    except (ValueError, TypeError):
        current_app.logger.error(
            f"/me route: Invalid identity format from token: {uid_str}"
        )
        return _json_error("无效的用户身份信息", 400)
    except Exception as e:
        current_app.logger.error(
            f"Error in /me route for identity {uid_str}: {e}", exc_info=True
        )
        return _json_error("获取用户信息时出错", 500)
