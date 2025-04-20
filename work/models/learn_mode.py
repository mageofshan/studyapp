import random
from difflib import SequenceMatcher

class LearnMode:
    def __init__(self, flashcards, length=10, answer_with='term', allow_typos=True):
        # initialize flashcards and settings
        self.flashcards = flashcards
        self.performance = {}
        self.length = length
        self.answer_with = answer_with
        self.allow_typos = allow_typos
        self.starred = set()
        
        # initialize performance for each flashcard
        for question in flashcards.keys():
            self.performance[question] = {'correct': 0, 'incorrect': 0}

    def star_term(self, term):
        """Mark a term as starred to increase its importance."""
        if term in self.flashcards:
            self.starred.add(term)
            return True
        # if doesn't exist, return False (avoid Error)
        return False
    
    def unstar_term(self, term):
        """Remove star from a term."""
        if term in self.starred:
            self.starred.remove(term)
            return True
        # if doesn't exist, return False (avoid Error)
        return False

    def get_next_question(self, level=1):
        """Select and generate the next question based on performance, starred terms, and question level."""
        # if no flashcards available (LearnMode hasn't started), return None
        if not self.flashcards:
            return None

        # get all questions    
        questions = list(self.flashcards.keys())
        
        # calculate weights based on performance and starred status
        weights = []
        for q in questions:
            # base weight is 1.0
            weight = 1.0
            
            # starred terms get double weight
            if q in self.starred:
                weight *= 2.0
                
            # adjust weight based on performance
            correct = self.performance[q]['correct']
            incorrect = self.performance[q]['incorrect']
            total = correct + incorrect
            
            if total > 0:
                # terms with lower accuracy get higher weight
                accuracy = correct / total
                weight *= (1.0 + (1.0 - accuracy))
            else:
                # new terms get higher weight
                weight *= 1.5
            # add all weights after calculation    
            weights.append(weight)
            
        # select question with weighted random choice
        question = random.choices(questions, weights=weights, k=1)[0]
        answer = self.flashcards[question]
        
        # Generate question based on level
        if level == 1:  # t/f
            if random.random() > 0.5:
                return {
                    'question': f"True or False: {question} means {answer}",
                    'answer': 'True',
                    'type': 'true_false'
                }
            else:
                other_answers = [value for key, value in self.flashcards.items() if key != question]
                if other_answers:
                    wrong_answer = random.choice(other_answers)
                    return {
                        'question': f"True or False: {question} means {wrong_answer}",
                        'answer': 'False',
                        'type': 'true_false'
                    }
                else:
                    return {
                        'question': f"True or False: {question} means {answer}",
                        'answer': 'True',
                        'type': 'true_false'
                    }
                
        elif level == 2:  # mcq
            options = [answer]
            other_answers = [value for key, value in self.flashcards.items() if key != question]
            
            if len(other_answers) >= 3:
                options.extend(random.sample(other_answers, 3))
            else:
                options.extend(other_answers)
                
            while len(options) < 4 and len(options) < len(self.flashcards) + 1:
                for value in self.flashcards.values():
                    if value not in options:
                        options.append(value)
                        break
                        
            random.shuffle(options)
            correct_index = options.index(answer)
            
            question_str = f"What does '{question}' mean?\n"
            for i, opt in enumerate(options):
                question_str += f"{chr(65+i)}) {opt}\n"
            
            return {
                'question': question_str,
                'answer': chr(65 + correct_index),
                'options': options,
                'type': 'multiple_choice'
            }
            
        elif level == 3:  # written response
            return {
                'question': f"Write the definition of: {question}",
                'answer': answer,
                'type': 'written'
            }
        
        # default case
        return {
            'question': f"Definition of {question}?",
            'answer': answer,
            'type': 'written'
        }

    def check_answer(self, question, user_answer):
        """Check the user's answer for correctness."""
        # if no flashcards available (LearnMode hasn't started), return None
        if question not in self.flashcards:
            return False
        
        # get the correct answer based on the user's answer type preference 
        correct_answer = self.flashcards[question] if self.answer_with == 'definition' else question
        
        # handle typo tolerance using SequenceMatcher
        if self.allow_typos:
            similarity = SequenceMatcher(None, correct_answer.lower(), user_answer.lower()).ratio()
            return similarity > 0.8
        
        # polished user friendly answer
        return correct_answer.lower().strip() == user_answer.lower().strip()

    def record_performance(self, question, correct):
        """Update performance based on the user's answer."""
        # if question not in performance (nothing answered), reset stats for question
        if question not in self.performance:
            self.performance[question] = {'correct': 0, 'incorrect': 0}

        # update performance stats    
        if correct:
            self.performance[question]['correct'] += 1
        else:
            self.performance[question]['incorrect'] += 1

    def generate_question(self, question, level=1):
        """Generate a question based on the specified level."""
        # if question not in performance (nothing answered), inform
        if question not in self.flashcards:
            return "Question not found in flashcards."
        
        # define answer    
        answer = self.flashcards[question]
        
        if level == 1:  # t/f
            # 50% chance of showing correct definition
            if random.random() > 0.5:
                return f"True or False: {question} means {answer}"
            else:
                # get a random different answer if available
                other_answers = [value for key, value in self.flashcards.items() if key != question]
                # if no other answers, return a false statement
                if other_answers:
                    wrong_answer = random.choice(other_answers)
                    return f"True or False: {question} means {wrong_answer}"
                else:
                    return f"True or False: {question} means {answer}"
                
        elif level == 2:  # mcq (multipe choice)
            # create a list of options
            options = []
            # include correct answer
            options.append(answer)
            
            # get a random different answer if available
            other_answers = [value for key, value in self.flashcards.items() if key != question]
            # if more than 3 other answers, randomly select 3
            if len(other_answers) >= 3:
                options.extend(random.sample(other_answers, 3))
                # if less than 3 options, still add (if 0 has no effect)
            else:
                options.extend(other_answers)
                
            # ensure at least 4 options
            while len(options) < 4 and len(options) < len(self.flashcards) + 1:
                for value in self.flashcards.values():
                    if value not in options:
                        options.append(value)
                        break
                        
            # shuffle options (not correct always first)
            random.shuffle(options)
            
            # create question string
            question_str = f"What does '{question}' mean?\n"
            for i, opt in enumerate(options):
                # capitalize option letter (A, B, C, D), then option
                question_str += f"{chr(65+i)}) {opt}\n"
            
            # return question string    
            return question_str
            
        elif level == 3:  # written Response
            return f"Write the definition of: {question}"
        
        # in case no level given, just return the question
        return f"Definition of {question}?"
    
    def get_performance_summary(self):
        """Return a summary of the user's performance with mastery levels."""
        # empty summary
        summary = {}
        # update summary with performance stats
        for question, stats in self.performance.items():
            total_attempts = stats['correct'] + stats['incorrect']
            accuracy = stats['correct'] / total_attempts if total_attempts > 0 else 0
            mastery = 'Mastered' if accuracy > 0.8 else 'Needs Improvement' if accuracy > 0.5 else 'Struggling'
            summary[question] = {
                'total_attempts': total_attempts,
                'accuracy': round(accuracy * 100, 1),  # Convert to percentage
                'mastery': mastery,
                'is_starred': question in self.starred
            }
        # return updated summary
        return summary

# example usage
# from scrapers.flashcard_scraper import get_flashcards
# url = "https://quizlet.com/9607765/ap-us-history-ch-4-flash-cards/?funnelUUID=26dcec1b-8e55-4eed-a84f-43265f09f07a"
# flashcards = get_flashcards(url)
# learn_mode = LearnMode(flashcards, length=5, answer_with='definition', allow_typos=True)
# question = learn_mode.get_next_flashcard()
# print(learn_mode.generate_question(question, level=2))
# correct = learn_mode.check_answer(question, "Some user answer")
# learn_mode.record_performance(question, correct)
# print(learn_mode.get_performance_summary())