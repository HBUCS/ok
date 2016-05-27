from flask import Blueprint, render_template
from server.extensions import cache
from flask.ext.rq import get_queue
from flask.ext.login import current_user

main = Blueprint('main', __name__)

@cache.cached(5000, unless=lambda: currrent_user.is_authenticated())
@main.route('/')
def home():
    return render_template('index.html')