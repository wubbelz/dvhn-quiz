document.addEventListener('DOMContentLoaded', () => {
    const welcomeScreen = document.getElementById('welcome-screen');
    const quizScreen = document.getElementById('quiz-screen');
    const resultsScreen = document.getElementById('results-screen');
    const startButton = document.getElementById('start-button');
    const playAgainButton = document.getElementById('play-again');
    const headlineElement = document.getElementById('headline');
    const optionsContainer = document.getElementById('options');
    const feedbackElement = document.getElementById('feedback');
    const progressBar = document.getElementById('progress-bar');
    const questionNumber = document.getElementById('question-number');
    const wordTypeElement = document.getElementById('word-type');
    
    let currentQuestion = 0;
    let gameData = [];
    let totalQuestions = 0;

    // Start the quiz
    startButton.addEventListener('click', async () => {
        try {
            const response = await fetch('/start');
            const data = await response.json();
            
            if (data.error) {
                alert(data.error);
                return;
            }
            
            gameData = data.game_data;
            totalQuestions = data.total_questions;
            currentQuestion = 0;
            
            welcomeScreen.classList.add('d-none');
            quizScreen.classList.remove('d-none');
            showQuestion();
        } catch (error) {
            console.error('Error starting quiz:', error);
            alert('Er is een fout opgetreden. Probeer het opnieuw.');
        }
    });

    // Play again
    playAgainButton.addEventListener('click', () => {
        resultsScreen.classList.add('d-none');
        welcomeScreen.classList.remove('d-none');
    });

    function showQuestion() {
        const question = gameData[currentQuestion];
        
        // Update progress
        const progress = ((currentQuestion + 1) / totalQuestions) * 100;
        progressBar.style.width = `${progress}%`;
        questionNumber.textContent = `Vraag ${currentQuestion + 1}/${totalQuestions}`;
        
        // Show headline
        headlineElement.textContent = question.censored_headline;
        
        // Show word type
        wordTypeElement.textContent = question.word_type === 'place' ? 
            'Raad de plaats die mist in deze krantenkop' : 
            'Raad de naam die mist in deze krantenkop';
        
        // Clear previous options and feedback
        optionsContainer.innerHTML = '';
        feedbackElement.classList.add('d-none');
        
        // Create option buttons
        question.options.forEach((option, index) => {
            const button = document.createElement('button');
            button.className = 'option-button col-12 col-md-6';
            button.textContent = option;
            button.addEventListener('click', () => checkAnswer(index));
            optionsContainer.appendChild(button);
        });
    }

    async function checkAnswer(answerIndex) {
        try {
            const response = await fetch('/check_answer', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    question_index: currentQuestion,
                    answer_index: answerIndex
                })
            });
            
            const data = await response.json();
            
            // Show feedback
            const feedback = document.createElement('div');
            feedback.className = `alert alert-${data.correct ? 'success' : 'danger'}`;
            
            const wordType = data.word_type === 'place' ? 'plaats' : 'naam';
            feedback.innerHTML = data.correct 
                ? `✨ Correct! De ontbrekende ${wordType} was inderdaad '${data.correct_word}'! 🎉`
                : `❌ Helaas! De ontbrekende ${wordType} was '${data.correct_word}' 😔`;
            feedbackElement.appendChild(feedback);
            feedbackElement.classList.remove('d-none');
            
            // Disable options
            const buttons = optionsContainer.querySelectorAll('.option-button');
            buttons.forEach((button, index) => {
                button.disabled = true;
                if (index === data.correct_index) {
                    button.classList.add('correct');
                } else if (index === answerIndex && !data.correct) {
                    button.classList.add('incorrect');
                }
            });
            
            // Wait before moving to next question
            setTimeout(() => {
                currentQuestion++;
                if (currentQuestion < totalQuestions) {
                    showQuestion();
                } else {
                    showResults();
                }
            }, 2000);
            
        } catch (error) {
            console.error('Error checking answer:', error);
            alert('Er is een fout opgetreden. Probeer het opnieuw.');
        }
    }

    async function showResults() {
        try {
            const response = await fetch('/get_results');
            const data = await response.json();
            
            quizScreen.classList.add('d-none');
            resultsScreen.classList.remove('d-none');
            
            // Update results display
            document.getElementById('score-display').textContent = 
                `🏆 Je score: ${data.score}/${data.total_questions}`;
            document.getElementById('percentage-display').textContent = 
                `📊 Percentage: ${data.percentage}%`;
            
            // Set appropriate message
            const messageDisplay = document.getElementById('message-display');
            if (data.percentage === 100) {
                messageDisplay.textContent = "🏆 Perfect! Je bent een nieuws expert! 🌟";
            } else if (data.percentage >= 80) {
                messageDisplay.textContent = "🎉 Geweldig! Je kent je nieuws heel goed! 📰";
            } else if (data.percentage >= 60) {
                messageDisplay.textContent = "👍 Goed gedaan! Blijf de krant lezen! 📚";
            } else {
                messageDisplay.textContent = "💪 Volgende keer beter! Blijf oefenen! 📖";
            }
            
        } catch (error) {
            console.error('Error getting results:', error);
            alert('Er is een fout opgetreden. Probeer het opnieuw.');
        }
    }
}); 