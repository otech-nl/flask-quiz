''' simple web app for quizes '''
from configparser import ConfigParser
import csv
from glob import glob
from os import path
from random import randint, shuffle

from flask import Flask, jsonify, render_template, request


class Quiz:
    ''' a quiz is a collection of facts '''
    def __init__(self, name, dir_name='data'):
        print(f'Reading {name}')
        self.facts = []
        file_name = path.join(dir_name, name)
        with open(f'{file_name}.csv', 'r') as data:
            reader = csv.DictReader(data)
            self.keys = reader.fieldnames
            for fact in reader:
                self.facts.append(fact)

        ini = ConfigParser()
        ini.read(f'{file_name}.ini')
        self.config = ini['config']

    @classmethod
    def read(cls, dir_name='data'):
        quizes = dict()
        for file_name in glob(f'{dir_name}/*.csv'):
            name = path.splitext(path.basename(file_name))[0]
            quizes[name] = Quiz(name, dir_name=dir_name)
        return quizes

    def get_question(self, nanswers=3):
        nfacts = len(self.facts)
        nr = randint(0, nfacts - 1)
        fact = self.facts[nr]
        key_nr = randint(1, len(self.keys) - 1)
        key = self.keys[key_nr]

        # setup answer and choices
        answer = fact[key]
        choices = [f for f in range(nfacts) if f != nr]
        shuffle(choices)
        choices = [answer] + [self.facts[i][key] for i in choices[:2]]
        shuffle(choices)

        return dict(
            question=f'Welke {key} hoort bij {fact[self.keys[0]]}?',
            answer=answer,
            choices=choices
        )


app = Flask('PyQuiz')
quizes = Quiz.read()


@app.route('/')
def index():
    return render_template(
        'index.jinja2',
        quizes=quizes
    )


@app.route('/question/<key>', methods=['GET', 'POST'])
def question(key):
    result = dict(counter=0, scores='0' * 10)
    message = 'Welkom bij deze quiz'

    if request.method == 'POST':
        form = request.form
        counter, scores = form.get('result').split(',')
        counter = int(counter) + 1
        if form.get('answer') == '0':
            message = '<b class="correct">Goed</b> geantwoord'
            scores += '1'
        else:
            message = '<b class="wrong">Fout</b> geantwoord'
            scores += '0'
        result = dict(counter=counter, scores=scores[-10:])
    result['score'] = sum(int(x) for x in result['scores'])
    quiz = quizes[key]
    question = quiz.get_question()

    return render_template('question.jinja2',
                           **question,
                           **result,
                           message=message,
    )


@app.route('/dump')
def dump():
    # global quizes
    quizes = Quiz.read()
    return jsonify({key: q.facts for key, q in quizes.items()})
