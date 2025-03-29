from flask import Flask, render_template, request, jsonify, session
from flask_session import Session
import requests
from bs4 import BeautifulSoup
import random
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this in production
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Dutch cities and places (add more as needed)
DUTCH_PLACES = {
    'Groningen', 'Leeuwarden', 'Assen', 'Emmen', 'Delfzijl', 'Winschoten', 'Veendam', 'Hoogeveen',
    'Meppel', 'Drachten', 'Heerenveen', 'Sneek', 'Zuidhorn', 'Hoogezand', 'Stadskanaal', 'Musselkanaal',
    'Ter Apel', 'Appingedam', 'Beilen', 'Coevorden', 'Roden', 'Schildwolde', 'Wildervank', 'Pekela',
    'Friesland', 'Drenthe', 'Nederland', 'Amsterdam', 'Rotterdam', 'Utrecht', 'Zwolle'
}

def is_place(word):
    """Check if a word is a place"""
    return word in DUTCH_PLACES

def is_name(word):
    """Check if a word is likely a name (capitalized word that's not a place)"""
    if word[0].isupper() and len(word) > 1:
        common_caps = {'De', 'Het', 'Een', 'LIVE', 'Dit', 'Dat', 'Deze', 'Die', 'Wat', 'Wie', 'Waar', 'FC'}
        return word not in common_caps and not is_place(word)
    return False

def get_word_type(word):
    """Determine if a word is a place or name"""
    if is_place(word):
        return 'place'
    elif is_name(word):
        return 'name'
    return None

def get_headlines():
    """Scrape headlines from dvhn.nl"""
    try:
        url = "https://www.dvhn.nl/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        headlines = []
        
        articles = soup.find_all('article')
        for article in articles:
            headline_elem = (
                article.find('h1') or 
                article.find('h2') or 
                article.find('h3') or 
                article.find('a', class_='title')
            )
            if headline_elem and headline_elem.text.strip():
                headlines.append(headline_elem.text.strip())
        
        return list(dict.fromkeys(headlines))[:15]
    except Exception as e:
        print(f"Error fetching headlines: {str(e)}")
        return []

def get_significant_word(headline):
    """Find a name or place in the headline to remove"""
    words = headline.split()
    significant_words = []
    
    for word in words:
        word_type = get_word_type(word)
        if word_type:
            significant_words.append((word, word_type))
    
    if significant_words:
        return random.choice(significant_words)
    return None

def generate_wrong_answers(correct_word, word_type, all_headlines):
    """Generate plausible wrong answers of the same type"""
    all_words = []
    
    # Collect words of the same type from headlines
    for headline in all_headlines:
        words = headline.split()
        for word in words:
            if get_word_type(word) == word_type and word != correct_word:
                all_words.append(word)
    
    # Add known places if we need more options
    if word_type == 'place':
        all_words.extend(list(DUTCH_PLACES))
    
    # Remove duplicates
    word_pool = list(set(all_words))
    
    # Select random words for wrong answers
    wrong_answers = random.sample(word_pool, min(3, len(word_pool)))
    
    # If we still don't have enough wrong answers, use some default places
    while len(wrong_answers) < 3 and word_type == 'place':
        random_place = random.choice(list(DUTCH_PLACES))
        if random_place not in wrong_answers and random_place != correct_word:
            wrong_answers.append(random_place)
    
    return wrong_answers

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start')
def start_game():
    headlines = get_headlines()
    valid_questions = []
    
    for headline in headlines:
        if get_significant_word(headline) is not None:
            valid_questions.append(headline)
    
    if len(valid_questions) < 5:
        return jsonify({'error': 'Niet genoeg koppen met namen of plaatsen gevonden'}), 400
    
    questions = random.sample(valid_questions, 5)
    game_data = []
    
    for headline in questions:
        removed_word, word_type = get_significant_word(headline)
        wrong_answers = generate_wrong_answers(removed_word, word_type, headlines)
        
        options = wrong_answers + [removed_word]
        random.shuffle(options)
        correct_index = options.index(removed_word)
        
        game_data.append({
            'headline': headline,
            'censored_headline': headline.replace(removed_word, '█' * len(removed_word)),
            'options': options,
            'correct_index': correct_index,
            'correct_word': removed_word,
            'word_type': word_type
        })
    
    session['game_data'] = game_data
    session['score'] = 0
    session['current_question'] = 0
    
    return jsonify({
        'game_data': game_data,
        'total_questions': len(game_data)
    })

@app.route('/check_answer', methods=['POST'])
def check_answer():
    data = request.get_json()
    question_index = data.get('question_index')
    answer_index = data.get('answer_index')
    
    game_data = session.get('game_data', [])
    if not game_data or question_index >= len(game_data):
        return jsonify({'error': 'Ongeldige vraag'}), 400
    
    question = game_data[question_index]
    is_correct = answer_index == question['correct_index']
    
    if is_correct:
        session['score'] = session.get('score', 0) + 1
    
    return jsonify({
        'correct': is_correct,
        'correct_word': question['correct_word'],
        'score': session.get('score', 0),
        'total_questions': len(game_data),
        'word_type': question['word_type']
    })

@app.route('/get_results')
def get_results():
    game_data = session.get('game_data', [])
    score = session.get('score', 0)
    total_questions = len(game_data)
    
    return jsonify({
        'score': score,
        'total_questions': total_questions,
        'percentage': round((score / total_questions) * 100, 1) if total_questions > 0 else 0
    })

if __name__ == '__main__':
    print("\nStarting DVHN News Quiz...")
    print("Access the quiz at: http://localhost:5000")
    print("Or from other devices on your network using your computer's IP address")
    app.run(host='0.0.0.0', port=5000, debug=True) 