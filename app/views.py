from app import app

import github
from github import Github, GithubException
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
        try :
            g = Github(form.username.data, form.password.data)
            global G
            G = g.get_user().get_repos()
        
            return redirect('/repos')
        except  github.BadCredentialsException:
            flash('Login Details are incorrect')
            pass
    return render_template('login.html', 
                           title='Sign In',
                           form=form)
@app.route('/repos')
def print_repos():
    try:
        global G
        if G:
            a = G
            G = None
            return render_template('repos.html', repos=a)
    except github.BadCredentialsException:
        flash('Login Details are incorrect')
    except Exception:
        flash('An unknown error has occured,  this may be because you have 2 factor authentication on')
    return redirect('/login')
