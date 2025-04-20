from flask import Flask, render_template, request, jsonify, redirect, url_for, session
#session for session values
from models.learn_mode import LearnMode
from scrapers.flashcard_scraper import scrape_flashcards
import json
import os #os for secure session

app = Flask(__name__)
# secure session
app.secret_key = os.urandom(24)

@app.route('/')
def index():
    return render_template('start.html', active_tab='start')

@app.route('/settings')
def settings():
    return render_template('settings.html', active_tab='settings')

@app.route('/learn')
def learn():
    return render_template('learn.html', active_tab='learn')

@app.route('/performance')
def performance():
    return render_template('performance.html', active_tab='performance', performance_summary=session.get('performance_summary', {}))

@app.route('/start_learn_mode', methods=['POST'])
def start_learn_mode():
    url = request.form.get('url')
    if not url:
        return jsonify({"error": "URL is required"}), 400
    try:
        # get flashcards from URL
        flashcards = scrape_flashcards(url)
        
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
        session['options'] =  None
        session['current_question'] = 0
        
        # force session update
        session.modified = True
        
        # open settings tab after start clicked
        return redirect(url_for('settings'))
    
    except Exception as e:
        return render_template('start.html', error=str(e), active_tab="start")

@app.route('/set_learn_mode_options', methods=['POST'])
def set_learn_mode_options():
    # check if learn mode started
    if 'flashcards' not in session:
        return render_template('start.html', error="Learn Mode not started", active_tab="start")

    # transfer learn mode options from request to session
    session['length'] = int(request.form.get('length', session.get('length')))
    session['answer_with'] = request.form.get('answer_with', session.get('answer_with', 'definition'))
    session['allow_typos'] = 'allow_typos' in request.form
    # split starred as comma-separated list and input
    starred_raw = request.form.get('starred', '')
    session['starred'] = [term.strip() for term in starred_raw.split(',') if term.strip()]

    # force session update
    session.modified = True

    # redirect to learn tab with question loaded
    return redirect(url_for('learn'))

@app.route('/get_flashcard', methods=['GET'])
def get_flashcard():
    # ensure learn mode started
    if 'flashcards' not in session:
        return render_template('start.html', error="Learn Mode has not been started.", active_tab="start")
    # Add debug check
    if not session['flashcards']:  # check if empty
        return render_template('start.html', error="No flashcards loaded.", active_tab="start")

    # create LearnMode instance with all relevant session data
    learn_mode = LearnMode(
        flashcards=session['flashcards'],
        length=session.get('length', 10),
        answer_with=session.get('answer_with', 'term'),
        allow_typos=session.get('allow_typos', True)
    )
    learn_mode.performance = session.get('performance', {})
    learn_mode.starred = set(session.get('starred', []))

    # get next question
    question_data = learn_mode.get_next_question(level=2)

    if not question_data:
        session.pop('question', None)
        session.pop('answer', None)
        # no more questions, show performance summary or redirect
        return render_template('performance.html', active_tab="performance", message="All questions completed!")


    # store question data in session
    session.update({
        'question': question_data['question'],
        'answer': question_data['answer'],
        'question_type': question_data['type'],
        'options': question_data.get('options', []),
        'performance': learn_mode.performance,  # save updated performance
        'starred': list(learn_mode.starred),    # save updated starred items
        'current_question': session.get('current_question', 0) + 1
    })
    session.modified = True

    # render learn template directly instead of redirecting
    return render_template('learn.html', active_tab="learn")

@app.route('/record_performance', methods=['POST'])
def record_performance():
    if 'flashcards' not in session:
        return render_template('learn.html', error="Learn Mode has not been started.", active_tab="learn")

    question = session.get('question')
    user_answer = request.form.get('answer')
    if not question or not user_answer:
        return render_template('learn.html', error="Missing question or answer.", active_tab="learn")

    learn_mode = LearnMode(
        session['flashcards'],
        length=session.get('length', 10),
        answer_with=session.get('answer_with', 'term'),
        allow_typos=session.get('allow_typos', True)
    )
    learn_mode.performance = session.get('performance', {})
    learn_mode.starred = set(session.get('starred', []))

    is_correct = learn_mode.check_answer(question, user_answer)
    learn_mode.record_performance(question, is_correct)
    session['performance'] = learn_mode.performance
    session.modified = True

    # if finished, redirect to performance
    if session.get('current_question', 0) >= session['length']:
        return redirect(url_for('performance'))

    # otherwise, redirect to get next flashcard
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
    term = request.args.get('term')
    
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