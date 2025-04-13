import random
from difflib import SequenceMatcher

class LearnMode:
    def __init__(self, flashcards, length=10, answer_with='definition', allow_typos=False):
        self.flashcards = flashcards
        self.performance = {}
        self.length = length
        self.answer_with = answer_with
        self.allow_typos = allow_typos
        self.starred = set()
        for question in flashcards.keys():
            self.performance[question] = {'correct': 0, 'incorrect': 0}

    def star_term(self, term):
        """Mark a term as starred to increase its importance."""
        self.starred.add(term)

    def get_next_flashcard(self):
        """Select the next flashcard based on performance and starred terms."""
        weights = [
            (2 if q in self.starred else 1) / (1 + self.performance[q]['correct'] - self.performance[q]['incorrect'])
            for q in self.flashcards.keys()
        ]
        return random.choices(list(self.flashcards.keys()), weights=weights, k=1)[0]

    def check_answer(self, question, user_answer):
        """Check the user's answer for correctness."""
        correct_answer = self.flashcards[question] if self.answer_with == 'definition' else question
        if self.allow_typos:
            similarity = SequenceMatcher(None, correct_answer.lower(), user_answer.lower()).ratio()
            return similarity > 0.8
        return correct_answer.lower() == user_answer.lower()

    def record_performance(self, question, correct):
        """Update performance based on the user's answer."""
        if correct:
            self.performance[question]['correct'] += 1
        else:
            self.performance[question]['incorrect'] += 1

    def generate_question(self, question, level=1):
        """Generate a question based on the specified level."""
        if level == 1:  # True/False
            return f"True or False: {question} means {self.flashcards[question]}"
        elif level == 2:  # Multiple Choice
            options = random.sample(list(self.flashcards.values()), 3)
            if self.flashcards[question] not in options:
                options[random.randint(0, 2)] = self.flashcards[question]
            random.shuffle(options)
            return f"What does {question} mean? Options: {', '.join(options)}"
        elif level == 3:  # Written Response
            return f"Write the definition of: {question}"

    def get_performance_summary(self):
        """Return a summary of the user's performance with mastery levels."""
        summary = {}
        for question, stats in self.performance.items():
            total_attempts = stats['correct'] + stats['incorrect']
            accuracy = stats['correct'] / total_attempts if total_attempts > 0 else 0
            mastery = 'Mastered' if accuracy > 0.8 else 'Needs Improvement' if accuracy > 0.5 else 'Struggling'
            summary[question] = {
                'total_attempts': total_attempts,
                'accuracy': accuracy,
                'mastery': mastery
            }
        return summary

# Example usage
# from scrapers.flashcard_scraper import get_flashcards
# url = "https://quizlet.com/9607765/ap-us-history-ch-4-flash-cards/?funnelUUID=26dcec1b-8e55-4eed-a84f-43265f09f07a"
# flashcards = get_flashcards(url)
# learn_mode = LearnMode(flashcards, length=5, answer_with='definition', allow_typos=True)
# question = learn_mode.get_next_flashcard()
# print(learn_mode.generate_question(question, level=2))
# correct = learn_mode.check_answer(question, "Some user answer")
# learn_mode.record_performance(question, correct)
# print(learn_mode.get_performance_summary())