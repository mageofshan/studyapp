# AI-Enhanced Study Application

This project is a modern, AI-enhanced web-based study application designed to provide a personalized and dynamic learning experience. It features:

- **Infinite Learn Mode**: Adaptive flashcard-based sessions using reinforcement learning and spaced repetition.
- **Flashcard Web Scraper**: Automatically extracts flashcards and notes from educational websites, PDFs, or pasted content.
- **Progress Tracking**: Visual dashboards to monitor learning progress.
- **Flashcard Set Management**: Save, organize, and share flashcard sets.
- **On-Device AI**: Powered by PyTorch for privacy and reduced server load.
- **Offline Mode**: Learn without an internet connection.
- **Smart Scheduling**: Suggests optimal review times for flashcards.

## Getting Started

1. Install the required Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   python app.py
   ```

## Project Structure

- `app.py`: Main application entry point.
- `models/`: Contains PyTorch models for reinforcement learning and spaced repetition.
- `static/`: HTML, CSS, and JavaScript files for the web interface.
- `scrapers/`: Web scraping utilities for extracting flashcards.
- `data/`: Stores user data and flashcard sets.

## Requirements

- Python 3.8+
- PyTorch

## License

This project is licensed under the MIT License.