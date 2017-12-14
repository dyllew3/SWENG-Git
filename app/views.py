
import collections
import datetime
import github
import json
import os

from bson import json_util
from app import app
from github import Github, GithubException
from flask import render_template, flash, redirect, session, url_for, request
from pathlib import Path


from .forms import GithubForm
from werkzeug.contrib.cache import SimpleCache

cache = SimpleCache()


class TimeoutException(Exception):
    pass


@app.route('/')
@app.route('/index')
def index():
    if 'username' in session and not cache.get(session['username']['user']):
        session.pop('username', None)
        
    return render_template('index.html', 
                           title='Index')

@app.route('/login', methods=["GET", "POST"])
def login():
    if 'username' in session:
        return redirect('/repos')
    form =  GithubForm()
    if form.validate_on_submit():
        try :
            g = Github(form.username.data, form.password.data)
            session['username'] = {'user':form.username.data}
            g.get_user()
            cache.set(form.username.data, g, timeout = 5*60)
            if get_repos():            
                return redirect('/repos')
        except  github.BadCredentialsException:
            flash('Login Details are incorrect')
        except TimeoutException:
            flash("Timeout has occured re-enter details")
    return render_template('login.html', 
                           title='Sign In',
                           form=form)
@app.route('/repos')
def print_repos():
    try:
        a = cache.get(session['username']['user'])
        if  not a:
            raise TimeoutException("")
        get_repos()
        pic = a.get_user().avatar_url
        a = a.get_user().get_repos()
        asd = collections.defaultdict(int)
        for r in a:
            if r.language:
                asd[r.language] += 1
            elif r.get_languages():
                for l in r.get_languages().keys():
                    asd[l] += 1

        data = []
        for k,v in asd.items():
            b = {}
            print((k,v))
            b['language'] = k
            b['amount'] = v
            data.append(b)
        return render_template('repos.html', repos=a, avatar_url=pic, data=data)
    except github.BadCredentialsException:
        flash('Login Details are incorrect')
        
    except TimeoutException:
        flash("Timeout has occured please re-enter details")
    except Exception as e:
        flash('An unknown error has occured,  this may be because you have 2 factor authentication on')
        flash(e)

    session.pop('username', None)        
    return redirect('/login')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/loc',methods=["GET", "POST"])
def loc():
    if 'username' not in session or not cache.get(session['username']['user']):
        return redirect(url_for('login'))
    g = cache.get(session['username']['user'])
    avatar_url = g.get_user().avatar_url
    cache.set(session['username']['user'],g,5*60 )
    data = None
    name = None
    if request.form.get('select_repo'):
        name = request.form.get('select_repo')
        data = get_data(request.form.get('select_repo'))
        
    return render_template('loc.html', rs=session['username']['repos'], title='Select Repo', avatar_url=avatar_url, data=data, name=name)



def get_repos():
    result = None
    if 'username' in session:
        try:
            session['username']['repos'] = []
            g = cache.get(session['username']['user'])
            if not g:
                raise TimeoutException("")
            repos = g.get_user().get_repos()
            for repo in repos:                
                session['username']['repos'].append(repo.full_name)
            return True
        except github.BadCredentialsException:
            flash("Invlaid details entered")
            logout()
        except GithubException as e:
            result = None
            flash(e)
            logout()
        except TimeoutException as e:
            result = None
            flash("Timeout re-enter details")
            logout()
    return result


def get_data(repo):
    data = []
    if 'username' in session:
        git = cache.get(session['username']['user'])
        cache.set(session['username']['user'], git, timeout=5*60)
        repo_obj = git.get_repo(repo)
        total = 0
        data = []
        i = 1
        if cache.get(repo) and repo in session['username']['repos']:
            data = cache.get(repo)[0]
            i = data[len(data) - 1]['commit'] + 1
        timestamp = datetime.datetime.now()
        commits = repo_obj.get_commits() if not data else repo_obj.get_commits(since=cache.get(repo)[1])
        for commit in commits.reversed:
            to_store = {}
            to_store['commit'] = i
            stat = commit.stats
            total += stat.additions - stat.deletions
            to_store['total'] = total
            to_store['add'] = stat.additions
            to_store['del'] = stat.deletions
            data.append(to_store)
            i += 1
        cache.set(repo,[data, timestamp], timeout=0)
        return [data, timestamp]
        
    else:
        return None


def read_from(filename):
    path = os.path.abspath('')
    full_name = "%s/app/static/%s" % (path,filename)
    my_file = Path(full_name)
    if my_file.is_file():
        return json.load(open(full_name), object_hook=json_util.object_hook)
    return None
    
def write_to(data,filename):
    if '/..' in filename:
        return None
    path = os.path.abspath('')
    full_name = "%s/app/static/%s" % (path,filename.replace('/','-'))
    with open(full_name, 'w+') as f:
        f.write(json.dumps(data, default=json_util.default))

@app.route('/temp')
def temp():
    return render_template('temp.html')

app.secret_key = '\x8b\x81fy\xba\xc1^OZ/\x02r3\x9el\xde\x085\xb0\xa5u\xfa\xfe\xfc'
