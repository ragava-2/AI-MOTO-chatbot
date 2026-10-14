# AI MOTO - Intelligent AI Vehicle Assistant

AI MOTO is a vehicle-focused AI assistant designed for bike and car owners who need quick, beginner-friendly troubleshooting guidance. The platform combines Flask-based web app functionality with AI-powered diagnostic support, image-based component inspection, and structured automotive knowledge.

This project is intended to help users:
- diagnose common vehicle issues
- understand component functions and maintenance needs
- inspect parts using uploaded images
- ask questions in a domain-specific automotive context
- access a vehicle learning mode for education and troubleshooting

For deeper product and architecture notes, see [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md).

---

## Features

- Bike and car-specific diagnostic workflows
- AI-powered chat responses for automotive problems
- Image upload support for visual vehicle part inspection
- Structured response format with summary, causes, checks, and action guidance
- Login and registration with JWT-based authentication
- Conversation history and session awareness
- Vehicle learning and maintenance explanations
- Multimedia-ready interface for text, image, and future voice workflows

---

## Tech Stack

- Python 3.10+
- Flask
- Flask-SQLAlchemy
- Flask-Bcrypt
- Flask-JWT-Extended
- Groq API
- Ultralytics / YOLO for image-based component detection
- SQLite database
- HTML, CSS, and JavaScript frontend

---

## Project Structure

```text
AI-chatbot/
├── app.py                     # Flask app entry point
├── extensions.py             # Flask extensions setup
├── requirements.txt          # Python dependencies
├── .env                      # Local environment variables
├── PROJECT_DOCUMENTATION.md  # Product and architecture documentation
├── chatbot/
│   ├── routes.py             # API endpoints and chat logic
│   ├── model.py              # AI model integration
│   ├── detector.py           # Vehicle/part detection logic
│   ├── image_retriever.py    # Image validation and enrichment
│   ├── knowledge_matcher.py # Automotive knowledge lookup
│   ├── memory.py             # Session memory logic
│   └── prompt.py             # Prompt templates
├── database/
│   └── models.py             # Database schema
├── data/                     # Knowledge and catalog data
├── static/                   # CSS, JS, uploaded UI assets
├── templates/                # Frontend HTML templates
├── scripts/                 # Utility scripts
├── weights/                  # YOLO model files
├── AI_MOTO_DATASET/         # Dataset folders
├── archive/                  # Historical or archived assets
├── runs/                     # Model detection outputs
├── tests/                   # Project tests (if added later)
└── instance/                 # Local runtime data
```

---

## Prerequisites

Before running the project, make sure you have:
- Python 3.10 or newer
- pip installed
- internet access for installing dependencies and the Groq API
- a Groq API key

---

## Environment Setup

1. Open a terminal in the project folder.
2. Create and activate a virtual environment:

```bash
python -m venv .venv
```

On Windows:

```bash
.venv\Scripts\activate
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create or update the `.env` file with required values:

```env
SECRET_KEY=your-super-secret-key
DATABASE_URL=sqlite:///chatbot.db
GROQ_API_KEY=your-groq-api-key
```

> The project already includes a `.env` file in this workspace, but you should keep the secret key private and rotate it if needed.

---

## Running the App

From the project directory:

```bash
python app.py
```

Then open the app in your browser:

```text
http://127.0.0.1:5000
```

The app serves core routes such as:
- `/` - landing page
- `/login` - login screen
- `/register` - registration screen
- `/history` - chat history view

---

## API Notes

The app exposes most backend logic under the `/api` blueprint. Common endpoints include:
- `/api/register`
- `/api/login`
- `/api/me`
- `/api/chat`

These endpoints support user authentication, chat responses, and vehicle diagnostic flows.

---

## Development Notes

- The app initializes the database automatically when started via `app.py`.
- The Flask app uses `db.create_all()` inside the `if __name__ == "__main__":` block.
- A local SQLite database file named `chatbot.db` is created automatically when the app starts.
- The project relies on model and dataset assets under the `weights/` and dataset folders for AI and visual workflows.

---

## Common Issues

### Missing Groq API key
If the AI services do not respond, verify that the `GROQ_API_KEY` value exists in `.env` and matches the key from your Groq account.

### Dependency install failures
Use a fresh virtual environment and ensure your Python version is compatible with the project requirements.

### Database errors
Delete the old SQLite file if needed and restart the app so the database is recreated with the current schema.

---

## License

This project is currently a local workspace application without a formal license file. If you plan to distribute or publish it, add an appropriate license before release.

---

## Contact / Use

This project is a custom automotive AI assistant for learning, diagnostics, and specialized vehicle support. It can be extended with richer voice support, more vehicle categories, or additional integrations.
