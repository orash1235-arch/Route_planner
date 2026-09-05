from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

VALID_INVITATION_CODES = ["OR2026", "NORTH-ADMIN", "TRIP-TEAM"]

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # If user hits register page while authenticated, log them out first or redirect
    if current_user.is_authenticated and request.method == 'GET':
        logout_user()

    form_data = {
        'user_id': '',
        'full_name': '',
        'phone_number': '',
        'invitation_code': ''
    }

    if request.method == 'POST':
        user_id = request.form.get('user_id', '').strip()
        full_name = request.form.get('full_name', '').strip()
        phone_number = request.form.get('phone_number', '').strip()
        password = request.form.get('password')
        repeat_password = request.form.get('repeat_password')
        invitation_code = request.form.get('invitation_code', '').strip()

        form_data = {
            'user_id': user_id,
            'full_name': full_name,
            'phone_number': phone_number,
            'invitation_code': invitation_code
        }

        if not all([user_id, full_name, phone_number, password, invitation_code]):
            flash("All fields are required.", "danger")
            return render_template('register.html', form_data=form_data)

        if password != repeat_password:
            flash("Passwords do not match.", "danger")
            return render_template('register.html', form_data=form_data)

        if invitation_code not in VALID_INVITATION_CODES:
            flash("Invalid invitation code.", "danger")
            return render_template('register.html', form_data=form_data)

        existing_user = User.query.get(user_id)
        if existing_user:
            flash("User ID already exists.", "danger")
            return render_template('register.html', form_data=form_data)

        new_user = User(
            id=user_id,
            full_name=full_name,
            phone_number=phone_number,
            password_hash=generate_password_hash(password),
            used_invitation_code=invitation_code
        )

        db.session.add(new_user)
        db.session.commit()

        # Log the user in via Flask-Login
        login_user(new_user)

        flash("Registration successful! Welcome aboard.", "success")
        return redirect(url_for('trips.list_trips'))

    return render_template('register.html', form_data=form_data)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # If user hits login page while authenticated, log them out first or redirect
    if current_user.is_authenticated and request.method == 'GET':
        logout_user()

    user_id_val = ''
    if request.method == 'POST':
        user_id = request.form.get('user_id', '').strip()
        password = request.form.get('password')
        user_id_val = user_id

        user = User.query.get(user_id)
        if user and check_password_hash(user.password_hash, password):
            # Log the user in via Flask-Login
            login_user(user)
            
            flash("Successfully logged in!", "success")
            next_page = request.args.get('next')
            return redirect(next_page or url_for('trips.list_trips'))

        flash("Invalid user ID or password.", "danger")

    return render_template('login.html', user_id=user_id_val)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for('auth.login'))