# main.py
from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
import os
from dotenv import load_dotenv
from square.client import Client
import uuid
import random
import time
import square
import flask
import openai
from pymongo import MongoClient
from flask import jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager 
import sys

# init SQLAlchemy so we can use it later in our models
from . import db

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['user_expenses']
expenses_collection = db['expenses']

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
openai.api_key = os.getenv("OPEN_AI_KEY")

main = Blueprint('main', __name__)

chat_history = []

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/profile')
@login_required
def profile():
    user = current_user.id
    return render_template('profile.html', name=current_user.first_name)


# Sample data to simulate user's budget and expenses
# budget = {
#     'income': 5000,
#     'categories': {
#         'Food': 500,
#         'Transportation': 300,
#         'Housing': 1000,
#         'Entertainment': 200
#     }
# }
# expenses = []

@main.route('/chart_data')
def chart_data():
    user_id = current_user.id  # Replace with the actual user_id
    expenses = expenses_collection.find({'user_id': user_id})

    for expense in expenses:
        budget = expense['budget']

    category_labels = budget['categories'].keys()
    category_amounts = budget['categories'].values()

    chart_data = {
        'labels': list(category_labels),
        'data': list(category_amounts)
    }

    return jsonify(chart_data)

@main.route('/income_data')
def income_data():
    user_id = current_user.id  # Replace with the actual user_id
    expenses = expenses_collection.find({'user_id': user_id})

    for expense in expenses:
        budget = expense['budget']

    income = budget['income']
    category_total = sum(budget['categories'].values())
    income_left = income-category_total

    chart_data = {
        'labels': ['Income remaining', 'Income spent'],
        'data': [income_left, category_total],
    }

    return jsonify(chart_data)

@main.route('/budgeting')
def budgeting():

    user_id = current_user.id  # Replace with the actual user_id
    expenses = expenses_collection.find({'user_id': user_id})

    for expense in expenses:
        budget = expense['budget']

    print(budget)
    return render_template('budgeting.html', budget=budget, expenses=expenses)

@main.route('/add_expense', methods=['POST'])
def add_expense():

    user_id = current_user.id  # Replace with the actual user_id
    category = request.form.get('category')
    amount = float(request.form.get('amount'))

    user_id = current_user.id  # Replace with the actual user_id
    expenses = expenses_collection.find({'user_id': user_id})
    # print(expenses)

    for expense in expenses:
        budget = expense['budget']

    budget['categories'][category] = amount

    # Create a new expense document
    expense = {
        'user_id': user_id,
        'budget': budget,
    }

    # Insert the expense document into MongoDB
    expenses_collection.insert_one(expense)

    return redirect(url_for('main.budgeting'))

@main.route('/financial_advice', methods=["POST", "GET"])
@login_required
def financial_advice():
    
    advice = ''

    openai.api_key = os.getenv("OPEN_AI_KEY")
    try:
        user_data = {
            'financial_situation': request.form['financial_situation'],
            'spending_patterns': request.form['spending_patterns'],
            'savings_goals': request.form['savings_goals']
        }

        ai_prompt = 'You are a an AI language model and I want you to provide some financial advice for me based on this information:\n'\
        +'- My spending patterns: "' + str(user_data['spending_patterns']) + '"\n- My current financial situation: "' + str(user_data['financial_situation'])\
        + '"\n- My current savings goals: "' + str(user_data['savings_goals']) + '"'

        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": ai_prompt}],
            max_tokens=100,
        )
        advice = completion.choices[0].message

        ai_prompt = ai_prompt[len('You are a an AI language model and I want you to provide some financial advice for me based on this information:\n'):]
        chat_history.append({'user_input': ai_prompt, 'response': advice['content']})

    except Exception as e:
        print(e)

    # Render the advice in a template
    return render_template('financial_advice.html', chat_history=chat_history)

