from app import app

from github import Github
from flask import render_template, flash, redirect
from .forms import GithubForm

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', 
                           title='Index')
G = None

@app.route('/login', methods=["GET", "POST"])
def login():
    form =  GithubForm()
    if form.validate_on_submit():
        g = Github(form.username.data, form.password.data)
        global G
        G = g.get_user().get_repos()
        #flash('Repos for %s are="%s"' %
        #      (form.username.data, str([str(x.language) + " " + x.full_name for x in g.get_user().get_repos()])))
        
        return redirect('/repos')
    return render_template('login.html', 
                           title='Sign In',
                           form=form)
@app.route('/repos')
def print_repos():
    global G
    if G:
        a = G
        G = None
        return render_template('repos.html', repos=a)
    return redirect('/login')
