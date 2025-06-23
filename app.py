from dotenv import load_dotenv
from flask_login import login_user, LoginManager, login_required, logout_user
from flask import Flask, render_template, request, render_template_string, flash, redirect, url_for
import os
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegisterForm, LoginForm
from models import db, User

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
login_manager = LoginManager()
login_manager.init_app(app)
db.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
@app.route('/',endpoint='index')
def homepage():
    users = User.query.all()
    return render_template('home.html', users=users)

@app.route('/contact')
def contact_page():
    return render_template('contact.html')

@app.route("/user/<int:user_id>")
def user_profile(user_id):
    user = User.query.get(user_id)
    if user:
        return render_template('components/user_detail.html', user=user)
    else:
        return render_template('404.html', message=f"user with id {user_id} not found"), 404



@app.route("/about")
def about():
    return render_template("about.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Неправильний email або пароль', 'danger')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()  # вихід користувача
    flash('Ви успішно вийшли з системи.', 'info')
    return redirect(url_for('login'))
@app.route("/register", methods=['GET', 'POST'],endpoint='register')
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        # 1. Отримуємо дані з форми
        name = form.name.data
        email = form.email.data
        password = form.password.data

        # 2. Створюємо нового користувача
        new_user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password)
        )

        # 3. Додаємо до сесії та зберігаємо в БД
        db.session.add(new_user)
        db.session.commit()

        # 4. Повідомлення і редірект
        flash("Реєстрація успішна!", "success")
        return redirect(url_for("login"))

    return render_template("register.html", form=form)


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html", message="page not found"), 404


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if User.query.count() == 0:
            demo_users = [
                User(
                    name="Oleh Solovey",
                    email="oleh@example.com",
                    bio="Enjoys early morning runs in the park.",
                    avatar_url="https://i.pravatar.cc/150?img=10",
                    password_hash=generate_password_hash("123456")
                ),
                User(
                    name="Iryna Kovalchuk",
                    email="iryna@example.com",
                    bio="Graphic designer and avid traveler.",
                    avatar_url="https://i.pravatar.cc/150?img=20",
                    password_hash=generate_password_hash("123456")
                ),
                User(
                    name="Nazar Bondarenko",
                    email="nazar@example.com",
                    bio="Working on a cybersecurity startup.",
                    avatar_url="https://i.pravatar.cc/150?img=30",
                    password_hash=generate_password_hash("123456")
                ),
                User(
                    name="Maria Lytvyn",
                    email="maria@example.com",
                    bio="Photographer and university lecturer.",
                    avatar_url="https://i.pravatar.cc/150?img=40",
                    password_hash=generate_password_hash("123456")
                ),
                User(
                    name="Artem Kostiuk",
                    email="artem@example.com",
                    bio="Writes code and listens to jazz music.",
                    avatar_url="https://i.pravatar.cc/150?img=50",
                    password_hash=generate_password_hash("123456")
                ),
            ]
            db.session.add_all(demo_users)
            db.session.commit()
    app.run(host='0.0.0.0',port=5000,debug=True)