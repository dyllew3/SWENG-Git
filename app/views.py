
import collections
import datetime
import github
from app import app
from github import Github, GithubException
from flask import render_template, flash, redirect, session, url_for, request

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
        
    return render_template('base.html', 
                           title='Index')

@app.route('/login', methods=["GET", "POST"])
def login():
    if 'username' in session:
        return redirect('/homepage')
    form =  GithubForm()
    if form.validate_on_submit():
        try :
            g = Github(form.username.data, form.password.data)
            session['username'] = {'user':form.username.data}
            g.get_user()
            cache.set(form.username.data, g, timeout = 15*60)
            if get_repos():            
                return redirect('/repos')
        except  github.BadCredentialsException:
            flash('Login Details are incorrect')
        except TimeoutException:
            flash("Timeout has occured re-enter details")
    return render_template('login.html', 
                           title='Sign In',
                           form=form)
@app.route('/homepage')
@app.route('/repos')
def print_repos():
    if 'username' not in session:
        flash("You must be logged in to visit that page")
        return redirect('/login')
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
    cache.set(session['username']['user'],g,15*60 )
    data = None
    # Get repo you want to query
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
        cache.set(session['username']['user'], git, timeout=15*60)
        repo_obj = git.get_repo(repo)
        total = 0
        data = []
        i = 1
        if cache.get(repo) and repo in session['username']['repos']:
            data = cache.get(repo)[0]
            i = data[len(data) - 1]['commit'] + 1
        timestamp = datetime.datetime.now()
        commits = repo_obj.get_commits() if not data else repo_obj.get_commits(since=cache.get(repo)[1], until=timestamp)
        # Get all commit stats since last time this was queried
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


@app.route('/repo/<string:user>/<string:name>')
def repo_data(user,name):
    if 'username' not in session:
        flash("Must be logged in to use that page")
        return redirect('/login')
    # Get user of repo
    new_g = Github(user) if user != session['username']['user'] else cache.get(session['username']['user'])
    if not new_g:
        flash("Timeout has occured please re-enter details")
        return redirect('/login')
    git_user = new_g.get_user()
    data = {'languages':{},'commit times':{}} 
    try:
        data['languages']['values'] = []
        data['languages']['commit times'] = []
        data['languages']['time'] = datetime.datetime.now()
        repo = git_user.get_repo(name)
        ls = repo.get_languages()
        # Get language stats
        for l in  repo.get_languages():
            l_dict = {'language':l, 'amount':ls[l]}
            data['languages']['values'] += [l_dict]
        if not ls:
            data['languages']['values'] = [{'language':'None', 'amount':repo.total}]
        return render_template('repo.html', title='Repo Info',rs=session['username']['repos'], data=data)

    except Exception:
        flash("An error has occured")
        return  redirect('/homepage')
    return name;


app.secret_key = '\x8b\x81fy\xba\xc1^OZ/\x02r3\x9el\xde\x085\xb0\xa5u\xfa\xfe\xfc'
