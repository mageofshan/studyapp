from flask import Flask, render_template, request, jsonify, redirect, url_for, session
#session for session values
from models.learn_mode import LearnMode
from scrapers.flashcard_scraper import get_flashcards
import json
import os
#os for secure session

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
        session['flashcards'] = flashcards  # dictionary of flashcards from url
        session['performance'] = {i: {'correct': 0, 'incorrect': 0} for i in session['flashcards'].keys()}  # nothing correct/incorrect yet
        session['starred'] = []  # nothing starred yet
        session['length'] = len(session['flashcards'])  # default length is the number of flashcards
        session['answer_with'] = 'term'  # default answer with term
        session['allow_typos'] = True  # default allow typos
        
        # force session update
        session.modified = True
        
        # open learn tab after start clicked
        return render_template('index.html', message="Learn Mode started successfully!", active_tab="settings")
    
    except Exception as e:
        return render_template('index.html', error=str(e), active_tab="start")

@app.route('/set_learn_mode_options', methods=['POST'])
def set_learn_mode_options():
    # check if learn mode started
    if 'flashcards' not in session:
        return jsonify({"error": "Learn Mode has not been started."}), 400
    
    # transfer learn mode options from request to session
    session['length'] = int(request.form.get('length', session.get('length', 10)))
    session['answer_with'] = request.form.get('answer_with', session.get('answer_with', 'definition'))
    session['allow_typos'] = 'allow_typos' in request.form
    # split starred as comma-separated list and input
    starred_raw = request.form.get('starred', '')
    session['starred'] = [term.strip() for term in starred_raw.split(',') if term.strip()]
    
    # force session update
    session.modified = True
    
    flashcard = None
    flashcard_data = get_flashcard()
    if flashcard_data:  # ensure flashcard data is not None
        flashcard = flashcard_data['question']  # pass only the question to the template

    # confirm settings update to user
    return render_template('index.html', message="Learn Mode settings updated successfully!", active_tab="learn", flashcard=flashcard)


@app.route('/next_flashcard', methods=['GET'])
def get_flashcard():
    # make sure learn mode started
    if 'flashcards' not in session:
        return None
    
    # create temporary LearnMode instance with session data for get_next_flashcard()
    learn_mode = LearnMode(
        session['flashcards'],
        length=session.get('length', 10),
        answer_with=session.get('answer_with', 'term'),
        allow_typos=session.get('allow_typos', True),
    )
    
    # transfer session data to LearnMode instance
    learn_mode.performance = session['performance']
    learn_mode.starred = set(session['starred'])
    
    # get next flashcard info
    question = learn_mode.get_next_flashcard()  # get the next question
    if not question:  # if no more flashcards, return None
        return None
    answer = session['flashcards'][question]  # get the answer for the question
    
    # return flashcard info
    return {"question": question, "answer": answer}

@app.route('/record_performance', methods=['POST'])
def record_performance():
    # make sure learn mode started
    if 'flashcards' not in session:
        return jsonify({"error": "Learn Mode has not been started."}), 400
    
    # get question and correct answer from request
    question = request.form.get('question')
    correct = request.form.get('correct') == 'true'
    
    if question not in session['flashcards']:
        return redirect(url_for('home', tab='learn'))
    
    # update performance in session
    if correct:
        session['performance'][question]['correct'] += 1
    else:
        session['performance'][question]['incorrect'] += 1
    
    # force session update
    session.modified = True
    
    # next flashcard
    return redirect(url_for('home', tab='learn'))

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