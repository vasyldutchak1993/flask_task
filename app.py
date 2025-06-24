from dotenv import load_dotenv
from flask_login import login_user, LoginManager, login_required, logout_user, current_user
from flask import Flask, render_template, request, render_template_string, flash, redirect, url_for
import os

from flask_socketio import SocketIO, emit, join_room
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegisterForm, LoginForm
from models import db, User, Message

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
login_manager = LoginManager()
login_manager.init_app(app)
db.init_app(app)
socketio = SocketIO(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

login_manager.login_view = 'login'  # ім'я ендпоінта для логіна

@login_manager.unauthorized_handler
def unauthorized_callback():
    flash("Будь ласка, увійдіть, щоб отримати доступ до цієї сторінки.", "warning")
    return redirect(url_for('login'))
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

@app.route('/chat',endpoint='chat')
@login_required
def chat():
    users = User.query.filter(User.id != current_user.id).all()
    return render_template('chat.html', users=users)


@app.route('/chat/<int:user_id>')
@login_required
def chat_with(user_id):
    user = User.query.get_or_404(user_id)

    # Всі повідомлення між current_user і user
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == user.id)) |
        ((Message.sender_id == user.id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.timestamp).all()

    return render_template("chat.html", user=user, messages=messages)

@socketio.on('private_message')
def handle_private_message(data):
    to_id = int(data['to'])
    content = data['content']

    msg = Message(sender_id=current_user.id, receiver_id=to_id, content=content)
    db.session.add(msg)
    db.session.commit()

    receiver = User.query.get(to_id)
    emit('receive_message', {
        'from_id': current_user.id,
        'from_name': current_user.name,
        'content': content
    }, room=f"user_{to_id}")

@socketio.on('connect')
def on_connect():
    if current_user.is_authenticated:
        join_room(f"user_{current_user.id}")


# @socketio.on('load_chat_history')
# def load_chat_history(data):
#     to_id = int(data['to'])
#     messages = Message.query.filter(
#         ((Message.sender_id == current_user.id) & (Message.receiver_id == to_id)) |
#         ((Message.sender_id == to_id) & (Message.receiver_id == current_user.id))
#     ).order_by(Message.timestamp).all()
#
#     history = [{
#         'sender_name': User.query.get(m.sender_id).name,
#         'content': m.content
#     } for m in messages]
#
#     emit('chat_history', {'messages': history})
@socketio.on('load_chat_history')
def load_chat_history(data):
    to_id = int(data['to'])
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == to_id)) |
        ((Message.sender_id == to_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.timestamp).all()

    history = [{
        'sender_id': m.sender_id,
        'sender_name': User.query.get(m.sender_id).name,
        'content': m.content
    } for m in messages]

    emit('chat_history', {'messages': history, 'current_user_id': current_user.id})


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
    # app.run(host='0.0.0.0',port=5000,debug=True)
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)