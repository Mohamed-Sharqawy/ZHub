from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from . import auth_bp
from .forms import LoginForm
from ..models import User


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.home'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Your account has been deactivated. Contact an administrator.', 'danger')
                return redirect(url_for('auth.login'))
            login_user(user, remember=form.remember_me.data)
            flash(f'Welcome back, {user.first_name}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('auth.home'))
        flash('Invalid email or password.', 'danger')

    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/')
@login_required
def home():
    return render_template('home.html')
