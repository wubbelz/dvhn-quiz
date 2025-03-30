from flask import Flask, render_template, request, jsonify, session
from flask_session import Session
import requests
from bs4 import BeautifulSoup
import random
from datetime import datetime
import socket
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')  # Use environment variable in production
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Dutch cities and places
DUTCH_PLACES = {
    # Groningen
    'Groningen', 'Leeuwarden', 'Assen', 'Emmen', 'Delfzijl', 'Winschoten', 'Veendam', 'Hoogeveen',
    'Meppel', 'Drachten', 'Heerenveen', 'Sneek', 'Zuidhorn', 'Hoogezand', 'Stadskanaal', 'Musselkanaal',
    'Ter Apel', 'Appingedam', 'Edam', 'Beilen', 'Coevorden', 'Roden', 'Schildwolde', 'Wildervank', 'Pekela',
    # Toegevoegde plaatsen in Groningen
    'Appingedam', 'Baflo', 'Bedum', 'Delfzijl', 'Eelde', 'Haren', 'Hoogkerk', 'Leek', 'Loppersum', 'Middelstum',
    'Oosterwolde', 'Sappemeer', 'Siddeburen', 'Ten Boer', 'Uithuizen', 'Winsum', 'Zuidhorn',
    # Friesland
    'Harlingen', 'Franeker', 'Dokkum', 'Lemmer', 'Bolsward', 'Workum', 'IJlst', 'Sloten',
    # Toegevoegde plaatsen in Friesland
    'Akkrum', 'Burgum', 'Gorredijk', 'Grou', 'Joure', 'Kollum', 'Makkum', 'Stiens', 'Surhuisterveen', 'Wolvega',
    # Drenthe
    'Meppel', 'Emmen', 'Hoogeveen', 'Assen', 'Coevorden',
    # Toegevoegde plaatsen in Drenthe
    'Beilen', 'Borger', 'Diever', 'Eelde', 'Gieten', 'Norg', 'Roden', 'Ruinen', 'Vries', 'Zuidlaren',
    # Overijssel
    'Enschede', 'Zwolle', 'Deventer', 'Almelo', 'Hengelo', 'Kampen', 'Oldenzaal', 'Ommen',
    # Gelderland
    'Nijmegen', 'Arnhem', 'Apeldoorn', 'Ede', 'Doetinchem', 'Zutphen', 'Wageningen', 'Harderwijk',
    # Utrecht
    'Utrecht', 'Amersfoort', 'Zeist', 'Nieuwegein', 'Veenendaal', 'Hilversum', 'Soest', 'Baarn',
    # Noord-Holland
    'Amsterdam', 'Haarlem', 'Zaandam', 'Alkmaar', 'Hilversum', 'Hoorn', 'Purmerend', 'Amstelveen',
    # Zuid-Holland
    'Rotterdam', 'Den Haag', 'Leiden', 'Delft', 'Dordrecht', 'Gouda', 'Schiedam', 'Vlaardingen',
    # Zeeland
    'Middelburg', 'Vlissingen', 'Goes', 'Terneuzen', 'Zierikzee', 'Veere', 'Tholen', 'Sluis',
    # Noord-Brabant
    'Eindhoven', 'Tilburg', 'Breda', 'Den Bosch', 'Helmond', 'Roosendaal', 'Oss', 'Bergen op Zoom',
    # Limburg
    'Maastricht', 'Venlo', 'Roermond', 'Heerlen', 'Sittard', 'Weert', 'Kerkrade',
    # Flevoland
    'Almere', 'Lelystad', 'Emmeloord', 'Dronten', 'Zeewolde', 'Urk', 'Biddinghuizen',
    # Provincies
    'Friesland', 'Drenthe', 'Overijssel', 'Gelderland', 'Utrecht', 'Noord-Holland', 'Zuid-Holland',
    'Zeeland', 'Noord-Brabant', 'Limburg', 'Flevoland', 'Groningen'
}

def is_place(word):
    """Check if a word is a place"""
    return word in DUTCH_PLACES

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

def get_place_from_headline(headline):
    """Find a place in the headline to remove"""
    words = headline.split()
    places = []
    
    # Check each word and its combinations
    for i, word in enumerate(words):
        # Check single word
        if is_place(word):
            places.append(word)
        
        # Check two-word combinations
        if i < len(words) - 1:
            two_words = f"{word} {words[i + 1]}"
            if is_place(two_words):
                places.append(two_words)
    
    return random.choice(places) if places else None

def generate_wrong_answers(correct_place):
    """Generate plausible wrong answers (other places)"""
    # Remove the correct place from the pool
    available_places = [place for place in DUTCH_PLACES if place != correct_place]
    
    # Select 3 random places
    wrong_answers = random.sample(available_places, 3)
    
    return wrong_answers

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start')
def start_game():
    headlines = get_headlines()
    valid_questions = []
    
    for headline in headlines:
        if get_place_from_headline(headline) is not None:
            valid_questions.append(headline)
    
    if len(valid_questions) < 5:
        return jsonify({'error': 'Niet genoeg koppen met plaatsnamen gevonden'}), 400
    
    questions = random.sample(valid_questions, 5)
    game_data = []
    
    for headline in questions:
        removed_place = get_place_from_headline(headline)
        wrong_answers = generate_wrong_answers(removed_place)
        
        options = wrong_answers + [removed_place]
        random.shuffle(options)
        correct_index = options.index(removed_place)
        
        game_data.append({
            'headline': headline,
            'censored_headline': headline.replace(removed_place, '█' * len(removed_place)),
            'options': options,
            'correct_index': correct_index,
            'correct_word': removed_place,
            'word_type': 'place'  # Always place
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
        'word_type': 'place'  # Always place
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
    # Get local IP address
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    print("\n=== DVHN Nieuws Quiz ===")
    print("\nJe kunt de quiz nu spelen op:")
    print(f"1. Lokaal op je computer: http://localhost:5000")
    print(f"2. Vanaf andere apparaten op je netwerk: http://{local_ip}:5000")
    print("\nOm de quiz te delen met anderen:")
    print("1. Zorg dat je computer en de andere apparaten op hetzelfde netwerk zitten")
    print("2. Deel de URL http://" + local_ip + ":5000 met anderen")
    print("3. Als anderen de quiz niet kunnen bereiken, controleer dan je firewall instellingen")
    print("\nDruk Ctrl+C om de quiz te stoppen")
    print("=" * 30 + "\n")
    
    # Use environment variable for port in production
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)