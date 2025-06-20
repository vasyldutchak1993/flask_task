from flask import Flask, render_template
from models import db, User

app = Flask(__name__)
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
@app.route('/')
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
                    avatar_url="https://i.pravatar.cc/150?img=10"
                ),
                User(
                    name="Iryna Kovalchuk",
                    email="iryna@example.com",
                    bio="Graphic designer and avid traveler.",
                    avatar_url="https://i.pravatar.cc/150?img=20"
                ),
                User(
                    name="Nazar Bondarenko",
                    email="nazar@example.com",
                    bio="Working on a cybersecurity startup.",
                    avatar_url="https://i.pravatar.cc/150?img=30"
                ),
                User(
                    name="Maria Lytvyn",
                    email="maria@example.com",
                    bio="Photographer and university lecturer.",
                    avatar_url="https://i.pravatar.cc/150?img=40"
                ),
                User(
                    name="Artem Kostiuk",
                    email="artem@example.com",
                    bio="Writes code and listens to jazz music.",
                    avatar_url="https://i.pravatar.cc/150?img=50"
                ),
            ]
            db.session.add_all(demo_users)
            db.session.commit()
    app.run(host='0.0.0.0',port=5000,debug=True)