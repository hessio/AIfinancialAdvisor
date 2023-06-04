# auth.py

from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from .models import User
from . import db
import uuid
import sys
import re
import square
from dotenv import load_dotenv
from square.client import Client
import os
import requests

auth = Blueprint('auth', __name__)

# Load environment variables from .env file
load_dotenv()

# Square API credentials
access_token = os.getenv('ACCESS_TOKEN') 
location_id = os.getenv('LOCATION_ID')

# Square API client object
square_client = Client(
    access_token=access_token,
    environment='sandbox'
)

@auth.route('/login')
def login():
    return render_template('login.html')

@auth.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    user = User.query.filter_by(email=email).first()

    # check if user actually exists
    # take the user supplied password, hash it, and compare it to the hashed password in database
    if not user or not check_password_hash(user.password, password): 
        flash('Please check your login details and try again.')
        return redirect(url_for('auth.login')) # if user doesn't exist or password is wrong, reload the page

    # if the above check passes, then we know the user has the right credentials
    login_user(user, remember=remember)
    return redirect(url_for('main.profile'))

@auth.route('/signup')
def signup():
    return render_template('signup.html')

@auth.route('/signup', methods=['POST'])
def signup_post():

    email = request.form.get('email')
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    postal_code = request.form.get('post_code')
    address_1 = request.form.get('address_1')
    address_2 = request.form.get('address_2')
    address_3 = request.form.get('address_3')
    password = request.form.get('password')
    phone = request.form.get('phone')

    if len(first_name) < 2 or len(last_name) < 2 or len(postal_code) < 2 or len(address_1) < 2 or len(address_2) < 2: # if a user is found, we want to redirect back to signup page so user can try again  
        flash('You must enter valid details')
        return redirect(url_for('auth.signup'))

    if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
        flash('You must enter a valid email address')
        return redirect(url_for('auth.signup'))

    user = User.query.filter_by(email=email).first() # if this returns a user, then the email already exists in database

    if user: # if a user is found, we want to redirect back to signup page so user can try again  
        flash('Email address already exists')
        return redirect(url_for('auth.signup'))

    result = square_client.customers.create_customer(
        body = {
            "idempotency_key": str(uuid.uuid4()),
            "given_name": first_name,
            "family_name": last_name,
            "email_address": email,
            "address": {
                "address_line_1": address_1,
                "address_line_2": address_2,
                "address_line_3": address_3,
                "postal_code": postal_code,
                "first_name": first_name,
                "last_name": last_name,
            },
            "phone_number": phone,
        }
    )

    cust_id = result.body['customer']['id']

    create_card = square_client.cards.create_card(
      body = {
        "idempotency_key": str(uuid.uuid4()),
        "source_id": "cnon:card-nonce-ok",
        "card": {
          "billing_address": {
            "address_line_1": address_1,
            "address_line_2": address_2,
            "address_line_3": address_3,
            "postal_code": postal_code,
            "country": "IE",
            "first_name": first_name,
            "last_name": last_name,
          },
          "customer_id": cust_id
        }
      }
    )

    card_id=create_card.body['card']['id']

    plan_id = 'M2Q7HAMHDRDGF6RWGC5HI5T5'
    data = {'idempotency_key': str(uuid.uuid4) + '_subscription', 'location_id': location_id,
        'plan_id': plan_id, 'customer_id': cust_id}
    
    # response = requests.post(f'https://connect.squareup.com/v2/subscriptions', headers=headers, json=data)
    response = square_client.subscriptions.create_subscription(
      body = {
        "location_id": location_id,
        "plan_id": plan_id,
        "customer_id": cust_id,
        "card_id": card_id,
      }
    )

    subscription_id = response.body['subscription']['id']

    # create new user with the form data. Hash the password so plaintext version isn't saved.
    new_user = User(id=str(uuid.uuid1()), email=email, first_name=first_name, last_name=last_name,
        password=generate_password_hash(password, method='sha256'),
        square_cust_id=cust_id, subscription_id=subscription_id, card_id=card_id)

    # add the new user to the database
    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('auth.login'))

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

