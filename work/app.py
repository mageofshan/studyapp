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
    return render_template('index.html')

@app.route('/start_learn_mode', methods=['POST'])
def start_learn_mode():
    # check if request is JSON
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    # url value
    url = request.json.get('url')
    if not url:
        return jsonify({"error": "URL is required"}), 400
    try:
        # get flashcards from URL
        flashcards = get_flashcards(url)
        
        # store flashcards in session
        session['flashcards'] = {key: value for key, value in flashcards.items()}
        session['performance'] = {i: {'correct': 0, 'incorrect': 0} for i in flashcards.keys()}
        session['starred'] = []
        session['length'] = 10
        session['answer_with'] = 'definition'
        session['allow_typos'] = False
        
        return jsonify({
            "message": "Learn Mode started successfully!", 
            "flashcards_count": len(flashcards)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/next_flashcard', methods=['GET'])
def next_flashcard():
    # make sure learn mode started
    if 'flashcards' not in session:
        return jsonify({"error": "Learn Mode has not been started."}), 400
    
    # create temporary LearnMode instance with session data
    learn_mode = LearnMode(
        session['flashcards'],
        length=session.get('length', 10),
        answer_with=session.get('answer_with', 'definition'),
        allow_typos=session.get('allow_typos', False)
    )
    
    # transfer session data to session
    learn_mode.performance = session['performance']
    learn_mode.starred = set(session['starred'])
    
    # get next flashcard info
    question = learn_mode.get_next_flashcard() #from learn_mode.py, puts learning weightage and starred in consideration
    answer = session['flashcards'][question]
    
    # return flashcard info
    return jsonify({
        "question": question,
        "answer": answer,
        #considering the following
        #"learning_weightage": learn_mode.get_learning_weightage(question),
        #"starred": question in learn_mode.starred
    })

@app.route('/record_performance', methods=['POST'])
def record_performance():
    # make sure learn mode started
    if 'flashcards' not in session:
        return jsonify({"error": "Learn Mode has not been started."}), 400
    
    # check if request is JSON
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    # get question and correct answer from request
    data = request.json
    question = data.get('question')
    correct = data.get('correct')
    
    if question not in session['flashcards']:
        return jsonify({"error": "Invalid question"}), 400
    
    # update performance in session
    if correct:
        session['performance'][question]['correct'] += 1
    else:
        session['performance'][question]['incorrect'] += 1
    
    # force session update
    session.modified = True
    
    # confirm
    return jsonify({"message": "Performance recorded successfully!"})

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

@app.route('/set_learn_mode_options', methods=['POST'])
def set_learn_mode_options():
    # check if learn mode started
    if 'flashcards' not in session:
        return jsonify({"error": "Learn Mode has not been started."}), 400
    # check if request is JSON
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    # transfer learn mode options from request to session
    data = request.json
    session['length'] = int(data.get('length', session.get('length', 10)))
    session['answer_with'] = data.get('answer_with', session.get('answer_with', 'definition'))
    session['allow_typos'] = data.get('allow_typos', session.get('allow_typos', False))
    
    # force session update
    session.modified = True
    
    # confirm settings update to user
    return jsonify({"message": "Learn Mode options updated successfully!"})

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

@app.route('/generate_question', methods=['POST'])
def generate_question():
    # check if learn mode started
    if 'flashcards' not in session:
        return jsonify({"error": "Learn Mode has not been started."}), 400
    
    # check if request is JSON
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    # get question and level from request
    data = request.json
    question = data.get('question')
    level = int(data.get('level', 1))
    
    # check if question exists
    if question not in session['flashcards']:
        return jsonify({"error": f"Question '{question}' not found in flashcards."}), 400
    
    # create temporary LearnMode instance
    learn_mode = LearnMode(session['flashcards'])
    generated_question = learn_mode.generate_question(question, level)
    
    # return jsonified generated question
    return jsonify({
        "question": generated_question,
        "original_question": question,
        "level": level
    })

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