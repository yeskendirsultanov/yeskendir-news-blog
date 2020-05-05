from flask import Flask
from flask import request
from flask import render_template
from loginform import LoginForm
from registerform import RegisterForm
from newsform import NewsForm
import json
from flask import redirect 
from data import db_session
from data.users import User
from data.news import News
from flask import make_response 
from flask import session
import datetime
from flask_login import LoginManager, login_user, current_user, login_required, logout_user
from flask_restful import abort

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)

app.permanent_session_lifetime = datetime.timedelta(days=365)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key' 

def main():
    db_session.global_init("db/blogs.sqlite")
    
    @login_manager.user_loader
    def load_user(user_id):
        session = db_session.create_session()
        return session.query(User).get(user_id)
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            session = db_session.create_session()
            user = session.query(User).filter(User.email == form.email.data).first()
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember_me.data)
                return redirect("/")
            return render_template('login.html',
                                   message="Неправильный логин или пароль",
                                   form=form)
        return render_template('login.html', title='Авторизация', form=form)
    
    @app.route('/register', methods=['GET', 'POST'])
    def reqister():
        form = RegisterForm()
        if form.validate_on_submit():
            if form.password.data != form.password_again.data:
                return render_template('register.html', title='Регистрация',
                                       form=form,
                                       message="Пароли не совпадают")
            session_db = db_session.create_session()
            if session_db.query(User).filter(User.email == form.email.data).first():
                return render_template('register.html', title='Регистрация',
                                       form=form,
                                       message="Такой пользователь уже есть")
            user = User(
                name=form.name.data,
                email=form.email.data,
                about=form.about.data
            )
            user.set_password(form.password.data)
            session_db.add(user)
            session_db.commit()
            return redirect('/login')
        return render_template('register.html', title='Регистрация', form=form)    
    
    @app.route("/")
    def index():
        session = db_session.create_session()
        if current_user.is_authenticated:
            news = session.query(News).filter((News.user == current_user) | (News.is_private != True))
        else:
            news = session.query(News).filter(News.is_private != True)
        return render_template("index.html", news=news)
    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect("/")
    
    @app.route('/news', methods=['GET', 'POST'])
    @login_required
    def add_news():
        form = NewsForm()
        if form.validate_on_submit():
            session = db_session.create_session()
            news = News()
            news.title = form.title.data
            news.content = form.content.data
            news.is_private = form.is_private.data
            current_user.news.append(news)
            session.merge(current_user)
            session.commit()
            return redirect('/')
        return render_template('news.html', title='Добавление новости',
                               form=form)
    
    @app.route('/news/<int:id>', methods=['GET', 'POST'])
    @login_required
    def edit_news(id):
        form = NewsForm()
        if request.method == "GET":
            session = db_session.create_session()
            news = session.query(News).filter(News.id == id,
                                              News.user == current_user).first()
            if news:
                form.title.data = news.title
                form.content.data = news.content
                form.is_private.data = news.is_private
            else:
                abort(404)
        if form.validate_on_submit():
            session = db_session.create_session()
            news = session.query(News).filter(News.id == id,
                                              News.user == current_user).first()
            if news:
                news.title = form.title.data
                news.content = form.content.data
                news.is_private = form.is_private.data
                session.commit()
                return redirect('/')
            else:
                abort(404)
        return render_template('news.html', title='Редактирование новости', form=form)

    @app.route('/news_delete/<int:id>', methods=['GET', 'POST'])
    @login_required
    def news_delete(id):
        session = db_session.create_session()
        news = session.query(News).filter(News.id == id,
                                          News.user == current_user).first()
        if news:
            session.delete(news)
            session.commit()
        else:
            abort(404)
        return redirect('/')
    
    
    app.run(port=8080, host='127.0.0.1')
    
if __name__ == '__main__':
    main()