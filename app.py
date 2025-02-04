import os
import sys
import click

from flask import Flask, render_template, request, url_for, redirect, flash
from markupsafe import escape
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev'
WIN = sys.platform.startswith('win')
if WIN:  # compatible with Window system
    prefix = 'sqlite:///'
else:  # for mac/linux system
    prefix = 'sqlite:////'

app.config['SQLALCHEMY_DATABASE_URI'] = prefix + os.path.join(app.root_path, 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Turn off monitoring of model modifications
#Load configuration before extension class instantiation
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id): 
    user = User.query.get(int(user_id))  
    return user



@app.cli.command()  # 注册为命令，可以传入 name 参数来自定义命令
@click.option('--drop', is_flag=True, help='Create after drop.')  # 设置选项
def initdb(drop):
    """Initialize the database."""
    if drop:  # 判断是否输入了选项
        db.drop_all()
    db.create_all()
    click.echo('Initialized database.')  # 输出提示信息

@app.cli.command()
def forge():
    """Generate fake data."""
    db.create_all()

    # 全局的两个变量移动到这个函数内
    name = 'Immensee'
    movies = [
        {'title': 'My Neighbor Totoro', 'year': '1988'},
        {'title': 'Dead Poets Society', 'year': '1989'},
        {'title': 'A Perfect World', 'year': '1993'},
        {'title': 'Leon', 'year': '1994'},
        {'title': 'Mahjong', 'year': '1996'},
        {'title': 'Swallowtail Butterfly', 'year': '1996'},
        {'title': 'King of Comedy', 'year': '1999'},
        {'title': 'Devils on the Doorstep', 'year': '1999'},
        {'title': 'WALL-E', 'year': '2008'},
        {'title': 'The Pork of Music', 'year': '2012'},
    ]

    user = User(name=name)
    db.session.add(user)
    for m in movies:
        movie = Movie(title=m['title'], year=m['year'])
        db.session.add(movie)

    db.session.commit()
    click.echo('Done.')

@app.cli.command()
@click.option('--username', prompt=True, help='The username used to login.')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='The password used to login.')
def admin(username, password):
    """Create user."""
    db.create_all()

    user = User.query.first()
    if user is not None:
        click.echo('Updating user...')
        user.username = username
        user.set_password(password)  
    else:
        click.echo('Creating user...')
        user = User(username=username, name='Admin')
        user.set_password(password)  
        db.session.add(user)

    db.session.commit() 
    click.echo('Done.')

@app.route('/', methods=['GET', 'POST'])
@app.route('/index')
@app.route('/home')
def index():
    if request.method == 'POST': 
        if not current_user.is_authenticated:  
            return redirect(url_for('index'))
        title = request.form.get('title')  
        year = request.form.get('year')
        if not title or not year or len(year) > 4 or len(title) > 60:
            flash('Invalid input.') 
            return redirect(url_for('index'))  
        # save to db
        movie = Movie(title=title, year=year)  
        db.session.add(movie)  
        db.session.commit()  
        flash('Item created.')  
        return redirect(url_for('index'))  
    
    movies = Movie.query.all()  #read movie records
    return render_template('index.html', movies=movies)

@app.route('/user/<name>')
def user_page(name):
    return f'User: {escape(name)}'

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        name = request.form['name']

        if not name or len(name) > 20:
            flash('Invalid input.')
            return redirect(url_for('settings'))

        current_user.name = name
        # current_user return the database record object for the currently logged in user
        # equal to
        # user = User.query.first()
        # user.name = name
        db.session.commit()
        flash('Settings updated.')
        return redirect(url_for('index'))

    return render_template('settings.html')

@app.route('/movie/edit/<int:movie_id>', methods=['GET', 'POST'])
@login_required
def edit(movie_id):
    movie = Movie.query.get_or_404(movie_id)

    if request.method == 'POST':  
        title = request.form['title']
        year = request.form['year']

        if not title or not year or len(year) != 4 or len(title) > 60:
            flash('Invalid input.')
            return redirect(url_for('edit', movie_id=movie_id))  

        movie.title = title  
        movie.year = year  
        db.session.commit()  
        flash('Item updated.')
        return redirect(url_for('index'))  

    return render_template('edit.html', movie=movie)  

@app.route('/movie/delete/<int:movie_id>', methods=['POST']) 
@login_required  # view protection
def delete(movie_id):
    movie = Movie.query.get_or_404(movie_id)  
    db.session.delete(movie)  
    db.session.commit()  
    flash('Item deleted.')
    return redirect(url_for('index'))  

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('Invalid input.')
            return redirect(url_for('login'))

        #user = User.query.first()
        user = User.query.filter_by(username=username).first()
        # validation
        if user is None:
            flash('Invalid username or password.')
            return redirect(url_for('login'))
        
        if username == user.username and user.check_password(password):
            login_user(user)  
            flash('Login success.')
            return redirect(url_for('index'))  

        flash('Invalid username or password.')  
        return redirect(url_for('login'))  

    return render_template('login.html')

@app.route('/logout')
@login_required  # For view protection
def logout():
    logout_user()  
    flash('Goodbye.')
    return redirect(url_for('index'))  

@app.route('/test')
def test_url_for():
    print(url_for('hello'))
    print(url_for('user_page', name='James'))
    print(url_for('user_page', name='Alice'))
    print(url_for('test_url_for'))
    print(url_for('test_url_for', num=2))
    return 'Test page'

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404 

@app.context_processor
def inject_user():  # 函数名可以随意修改
    user = User.query.first()
    return dict(user=user)  # 需要返回字典，等同于 return {'user': user}

# Define database model
class Movie(db.Model):  
    id = db.Column(db.Integer, primary_key=True)  
    title = db.Column(db.String(60))  
    year = db.Column(db.String(4)) 

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    username = db.Column(db.String(20))  
    password_hash = db.Column(db.String(128))  

    def set_password(self, password):
        self.password_hash = generate_password_hash(
            password,
            method='pbkdf2:sha256'  
        )
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password) 
    
