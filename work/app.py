from flask import Flask, render_template, request, jsonify, redirect, url_for, session
#session for session values
from models.learn_mode import LearnMode
from scrapers.flashcard_scraper import get_flashcards
import json
import os #os for secure session

app = Flask(__name__)
# secure session
app.secret_key = os.urandom(24)

@app.route('/')
def home():
    tab = request.args.get('tab', 'start')  # default to 'start'
    return render_template('index.html', active_tab=tab)

@app.route('/start_learn_mode', methods=['POST'])
def start_learn_mode():
    # no JSON check (leads to not being read)
    url = request.form.get('url')
    if not url:
        return jsonify({"error": "URL is required"}), 400
    try:
        # get flashcards from URL
        flashcards = get_flashcards(url)
        
        # store flashcards in session
        session['flashcards'] = {key: value for key, value in flashcards.items()}  # dictionary of flashcards from url
        session['performance'] = {i: {'correct': 0, 'incorrect': 0} for i in session['flashcards'].keys()}  # nothing correct/incorrect yet
        session['starred'] = []  # nothing starred yet
        session['length'] = len(session['flashcards'])  # default length is the number of flashcards
        session['answer_with'] = 'term'  # default answer with term
        session['allow_typos'] = True  # default allow typos
        # both empty until get_flashcard is called
        session['question'] = None
        session['answer'] = None
        session['question_type'] = None
        session['options'] = None
        session['current_question'] = 0
        
        # force session update
        session.modified = True
        
        # open settings tab after start clicked
        return render_template('index.html', message="Learn Mode started successfully!", active_tab="settings")
    
    except Exception as e:
        return render_template('index.html', error=str(e), active_tab="start")

@app.route('/set_learn_mode_options', methods=['POST'])
def set_learn_mode_options():
    # check if learn mode started
    if 'flashcards' not in session:
        return jsonify({"error": "Learn Mode has not been started."}), 400
    
    # transfer learn mode options from request to session
    session['length'] = int(request.form.get('length', session.get('length')))
    session['answer_with'] = request.form.get('answer_with', session.get('answer_with', 'definition'))
    session['allow_typos'] = 'allow_typos' in request.form
    # split starred as comma-separated list and input
    starred_raw = request.form.get('starred', '')
    session['starred'] = [term.strip() for term in starred_raw.split(',') if term.strip()]

    # force session update
    session.modified = True

    # redirect to first flashcard instead of learn tab
    return redirect(url_for('get_flashcard'))

@app.route('/get_flashcard', methods=['GET'])
def get_flashcard():
    # make sure learn mode started
    if 'flashcards' not in session:
        return render_template('index.html', error="Learn Mode has not been started.", active_tab="learn")
    
    # create temporary LearnMode instance with session data for get_next_question()
    learn_mode = LearnMode(
        session['flashcards'],
        length=session.get('length', 10),
        answer_with=session.get('answer_with', 'term'),
        allow_typos=session.get('allow_typos', True),
    )
    
    # transfer session data to LearnMode instance
    learn_mode.performance = session['performance']
    learn_mode.starred = set(session['starred'])
    
    # get next question info
    question_data = learn_mode.get_next_question(level=2)  # default to multiple choice
    if not question_data:  # if no more questions, redirect to performance
        return redirect(url_for('home', tab='performance'))
    
    # store question data in session
    session['question'] = question_data['question']
    session['answer'] = question_data['answer']
    session['question_type'] = question_data['type']
    if 'options' in question_data:
        session['options'] = question_data['options']
    
    # update current question number
    session['current_question'] = session.get('current_question', 0) + 1
    
    # force session update
    session.modified = True
    
    # render template with question data
    return render_template('index.html', 
                         active_tab="learn",
                         question=question_data['question'],
                         question_type=question_data['type'],
                         options=question_data.get('options', []),
                         current_question=session['current_question'],
                         total_questions=session['length'])

@app.route('/record_performance', methods=['POST'])
def record_performance():
    # make sure learn mode started
    if 'flashcards' not in session:
        return render_template('index.html', error="Learn Mode has not been started.", active_tab="learn")
    
    # get question and user's answer from request
    question = request.form.get('question')
    user_answer = request.form.get('answer')

    if not question or not user_answer:
        return render_template('index.html', error="Missing question or answer.", active_tab="learn")
    
    # create temporary LearnMode instance
    learn_mode = LearnMode(
        session['flashcards'],
        length=session.get('length', 10),
        answer_with=session.get('answer_with', 'term'),
        allow_typos=session.get('allow_typos', True),
    )
    
    # transfer session data to LearnMode instance
    learn_mode.performance = session['performance']
    learn_mode.starred = set(session['starred'])
    
    # check if answer is correct
    is_correct = learn_mode.check_answer(question, user_answer)
    
    # record performance
    learn_mode.record_performance(question, is_correct)
    
    # update session with new performance data
    session['performance'] = learn_mode.performance
    
    # force session update
    session.modified = True
    
    # if we've reached the end, redirect to performance
    if session.get('current_question', 0) >= session['length']:
        return redirect(url_for('home', tab='performance'))
    
    # otherwise, get next question
    return redirect(url_for('get_flashcard'))

@app.route('/performance_summary', methods=['GET'])
def performance_summary():
    # make sure learn mode started
    if 'flashcards' not in session:
        return jsonify({"error": "Learn Mode has not been started."}), 400
    
     # fill performance summary dict
    summary = {}
    for question, stats in session['performance'].items():
        total_attempts = stats['correct'] + stats['incorrect']
        accuracy = stats['correct'] / total_attempts if total_attempts > 0 else 0
        mastery = 'Mastered' if accuracy > 0.8 else 'Needs Improvement' if accuracy > 0.5 else 'Struggling'
        summary[question] = {
            'total_attempts': total_attempts,
            'accuracy': round(accuracy * 100, 1),
            'mastery': mastery,
            'is_starred': question in session['starred']
        }
    
    #return jsonified summary
    return jsonify(summary)

@app.route('/star_term', methods=['POST'])
def star_term():
    # check if learn mode started
    if 'flashcards' not in session:
        return jsonify({"error": "Learn Mode has not been started."}), 400
    
    # check if request is JSON
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    # get term from request
    term = request.json.get('term')
    
    # check if term exists
    if term not in session['flashcards']:
        return jsonify({"error": f"Term '{term}' not found in flashcards."}), 400
    
    # add to starred if not already starred
    if term not in session['starred']:
        session['starred'].append(term)
        # force session update
        session.modified = True
        return jsonify({"message": f"Term '{term}' starred successfully!"})
    else:
        # remove from starred if already starred (unstar)
        session['starred'].remove(term)
        # force session update
        session.modified = True
        return jsonify({"message": f"Term '{term}' unstarred successfully!"})

@app.route('/clear_learn_mode', methods=['POST'])
def clear_learn_mode():
    # clear session data
    session.pop('flashcards', None) #returns None if not existing (avoid KeyError)
    session.pop('performance', None)
    session.pop('starred', None)
    session.pop('length', None)
    session.pop('answer_with', None)
    session.pop('allow_typos', None)
    
    # inform user of LearnMode clear
    return jsonify({"message": "Learn Mode cleared successfully!"})

# python app.py in terminal to run flask app
if __name__ == '__main__':
    app.run(debug=True)