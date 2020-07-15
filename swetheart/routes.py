from flask import request, render_template, redirect, flash, url_for
import re
import requests
from flask_login import login_user, login_required, logout_user, current_user
from newsapi import NewsApiClient
from werkzeug.security import check_password_hash, generate_password_hash

from swetheart import db, app
from swetheart.models import User, Crypto

from swetheart.go_data import card_dict


@app.route('/', methods=['GET'])
def index():
    if current_user.is_authenticated:
        user = User.query.filter_by(id=current_user.get_id()).first()
        list_crypto = [crypt.crypto_name for crypt in user.my_crypto]
        new_card_dict = {key: card_dict[key] for key in list_crypto}
    else:
        new_card_dict = card_dict
    return render_template('index.html', card_dict=new_card_dict)


@app.route('/stonks', methods=['GET', 'POST'])
def stonks():
    price = {'ETHUSDT': {'price': '', 'percent24': ''},
             'BTCUSDT': {'price': '', 'percent24': ''},
             'LTCUSDT': {'price': '', 'percent24': ''},
             'XRPUSDT': {'price': '', 'percent24': ''},
             }
    price_url = 'https://api.binance.com/api/v3/ticker/24hr'
    params = {'symbol': ''}
    for currency in price:
        params['symbol'] = currency
        req = requests.get(price_url, params=params).json()
        if req.get('code') == -1003:
            return {'error': -1003}
        price[currency]['price'] = req['lastPrice'][:7] + '$'
        price[currency]['percent24'] = re.sub(r'^\d.{4}', '+' + req['priceChangePercent'][:5],
                                              req['priceChangePercent'][:6]) + '%'
    return price

@app.route('/get_news/<jsdata>')
def get_news(jsdata):
    news = find_news(jsdata)
    return news

def find_news(flag):
    news_api = NewsApiClient(api_key='a4c854576fbc472e8f06265c455e1ae6')
    news = news_api.get_everything(q=flag, language='en')
    news = list(filter(lambda x: x['description'], news['articles']))
    return {'title': news[0]['title'], 'body': news[0]['description'], 'url': news[0]['url']}


@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if request.method == 'POST':
        name = request.form['user_name']
        password = request.form['user_password']
        password_2 = request.form['user_password_2']
        error = None

        if not name:
            error = 'User is required'
        elif not password:
            error = 'Password is required'
        elif password != password_2:
            error = 'Passwords are not equal'
        elif User.query.filter(User.name == name).first():
            error = 'User {} is already exist'.format(name)
        else:
            hash_pas = generate_password_hash(password)
            new_user = User(name=name, password=hash_pas)

        if error is None:
            try:
                db.session.add(new_user)
                db.session.commit()
                return redirect(url_for('index'))
            except:
                return 'Че-то пошло не так...'

        return error

    return render_template('registration.html')


@app.route('/users')
@login_required
def users():
    users = User.query.order_by(User.date).all()
    return render_template('users.html', users=users)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['user_name']
        password = request.form['user_password']

        user = User.query.filter(User.name == name).first()

        if user and check_password_hash(user.password, password):
            login_user(user)

            next_page = request.args.get('next')

            return redirect(url_for('index'))
        else:
            return 'Something is going wrong'

    return render_template('login.html')


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/collect_crypto', methods=['GET', 'POST'])
@login_required
def collect_crypto():
    if request.method == 'POST':
        user = User.query.filter_by(id=current_user.get_id()).first()
        user.my_crypto = []
        cur_list = [currency for currency in request.form]
        for cur in cur_list:
            c = Crypto.query.filter_by(crypto_name=cur).first()
            if not c:
                c = Crypto(crypto_name=cur)
            user.my_crypto.append(c)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('collect_crypto.html')


@app.after_request
def redirect_to_signin(response):
    if response.status_code == 401:
        return redirect(url_for('login'))
    return response