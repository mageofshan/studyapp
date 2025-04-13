from flask import Flask, render_template, request, jsonify
from models.learn_mode import LearnMode
from scrapers.flashcard_scraper import get_flashcards

app = Flask(__name__)

# Initialize LearnMode globally
learn_mode = None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/start_learn_mode', methods=['POST'])
def start_learn_mode():
    global learn_mode
    url = request.json.get('url')
    try:
        flashcards = get_flashcards(url)
        learn_mode = LearnMode(flashcards)
        return jsonify({"message": "Learn Mode started successfully!", "flashcards_count": len(flashcards)})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/next_flashcard', methods=['GET'])
def next_flashcard():
    if learn_mode is None:
        return jsonify({"error": "Learn Mode has not been started."}), 400
    question = learn_mode.get_next_flashcard()
    return jsonify({"question": question})

@app.route('/record_performance', methods=['POST'])
def record_performance():
    if learn_mode is None:
        return jsonify({"error": "Learn Mode has not been started."}), 400
    data = request.json
    question = data.get('question')
    correct = data.get('correct')
    learn_mode.record_performance(question, correct)
    return jsonify({"message": "Performance recorded successfully!"})

@app.route('/performance_summary', methods=['GET'])
def performance_summary():
    if learn_mode is None:
        return jsonify({"error": "Learn Mode has not been started."}), 400
    summary = learn_mode.get_performance_summary()
    return jsonify(summary)

@app.route('/set_learn_mode_options', methods=['POST'])
def set_learn_mode_options():
    if learn_mode is None:
        return jsonify({"error": "Learn Mode has not been started."}), 400
    data = request.json
    learn_mode.length = data.get('length', learn_mode.length)
    learn_mode.answer_with = data.get('answer_with', learn_mode.answer_with)
    learn_mode.allow_typos = data.get('allow_typos', learn_mode.allow_typos)
    return jsonify({"message": "Learn Mode options updated successfully!"})

@app.route('/star_term', methods=['POST'])
def star_term():
    if learn_mode is None:
        return jsonify({"error": "Learn Mode has not been started."}), 400
    term = request.json.get('term')
    learn_mode.star_term(term)
    return jsonify({"message": f"Term '{term}' starred successfully!"})

@app.route('/generate_question', methods=['POST'])
def generate_question():
    if learn_mode is None:
        return jsonify({"error": "Learn Mode has not been started."}), 400
    data = request.json
    question = data.get('question')
    level = data.get('level', 1)
    generated_question = learn_mode.generate_question(question, level)
    return jsonify({"question": generated_question})

if __name__ == '__main__':
    app.run(debug=True)