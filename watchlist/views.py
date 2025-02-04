from flask import render_template, request, url_for, redirect, flash
from flask_login import login_user, login_required, logout_user, current_user

from watchlist import app, db
from watchlist.models import User, Movie

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
