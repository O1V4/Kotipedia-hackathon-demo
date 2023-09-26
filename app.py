from sqlalchemy.sql import text
from flask import Flask, render_template, request, redirect, Response, stream_with_context
from flask_sqlalchemy import SQLAlchemy
from os import getenv
import psycopg2
import os
import openai
import time
from dotenv import load_dotenv


load_dotenv()
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URL")
db = SQLAlchemy(app)
openai.api_key = getenv("OPENAI_API_KEY")


def instructions(question, data_list):
    return f'''
    I'm going to give you 4 categories about home owner's housing data.
    The categories are related to electricity usage (something like kWh), house specs (like area, heating method),
    years related to the house (the year of construction and etc), and the last one is additional information that the user might want to give.

    The user will ask you a question related to his/her housing situation that is probably concerning energy consumption
    or repairments or new heating methods/systems or everyday sustainable living.

    We want you to answer with suggestions, recommendations and ideas as spesific and
    personal as possible based on the data from the user that was provided before the question.
    We want you to consider sustainable solutions and tips to the question the user asks.
    Keep your answer as concise, brief and to the point as possible (but also don't focus only on one keypoint).
    The most important parts of the answer are:
    1. try to use as many stats/numerical values for the reasoning as possible that are likely provided in the user's data and 
    2. strong emphasis on sustainability.


    Next will be the informatian that the user answered:

    1. Electricity consumption; electric bill, kWh usage, etc. (Required):
    "{data_list[0]}"

    2. House condition, heating system, square-meter size m^2, etc. (Required):
    "{data_list[1]}"

    3. Build year, most recent repair year, etc. (Required):
    "{data_list[2]}"

    4. Additional information (Optional):
    "{data_list[3]}"

    
    And now the user's question is the following:
    {question} 
    '''


@app.route("/")
def index():
    #result = db.session.execute(text("SELECT content FROM messages"))
    #messages = result.fetchall()
    return render_template("index.html") 

@app.route("/questions")
def questions():
    return render_template("questions.html")


@app.route("/data", methods=["POST"])
def data():
    q1 = request.form["comment1"]
    q2 = request.form["comment2"]
    q3 = request.form["comment3"]
    q4 = request.form["comment4"]
    params = {"electricity": q1, "condition": q2, "year": q3, "addition": q4}
    sql = text("INSERT INTO data (electricity,condition,year,addition) VALUES (:electricity,:condition,:year,:addition)")
    db.session.execute(sql, params)
    db.session.commit()
    return redirect("/questions")


@app.route("/ask", methods=["POST"])
def ask():
    user_ask = request.form["question"]
    result = db.session.execute(text("SELECT * FROM data ORDER BY id DESC LIMIT 1;"))
    row = result.fetchone()
    list_help = []
    for i in range(1,5):
        list_help.append(str(row[i])) 

    def generate():
        delay_time = 0.01
        answer = ""
        response = openai.ChatCompletion.create(
            model="gpt-4", 
            messages=[{"role": "user", "content": instructions(user_ask,list_help)}],
            stream=True
            )
        yield render_template("header.html", text=answer)
        for event in response:
            event_text = event['choices'][0]['delta']
            answer = event_text.get('content', '')
            yield render_template("footer.html", text=answer)
            print(answer)
            time.sleep(delay_time)
    
    return Response(stream_with_context(generate()), content_type='text/html')
    
    
    #return render_template("ask.html", text = chat_completion["choices"][0]["message"]["content"])

