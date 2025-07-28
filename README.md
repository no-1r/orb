# Orb
<img width="1244" height="750" alt="image" src="https://github.com/user-attachments/assets/32b926a7-f5e1-4732-9ece-d7456aef0733" />

> Have you ever seen memes of this dude and thought: "Damn, I want to try that, that looks fun!"

A mystical web app where users anonymously share thoughts and drawings. Touch the orb to glimpse random submissions from others, or contribute your own prophecies to the eternal collection.

**[Live Demo](https://your-railway-url.up.railway.app)** | **[Run Locally](#local-setup)**

## Features

- **Scrying**: Touch the orb to reveal random anonymous submissions
- **Prophecy Creation**: Share text or hand-drawn visions  
- **Canvas Drawing**: Draw directly in browser with customizable tools
- **Floating Wizard**: Interactive tutorial guide
- **Gothic Aesthetic**: Pixelated medieval fonts and dark fantasy design
- **Magical Animations**: Content emerges dramatically from within the orb

## Tech Stack

- **Backend**: Flask (Python) + SQLite
- **Frontend**: HTML5 Canvas + Vanilla JS
- **Security**: PIL image processing, parameterized queries
- **Deployment**: Railway

## Online Demo

Visit the live version at **https://orb.up.railway.app/**

No installation required - just open and start scrying.

## Local Setup

```bash
git clone https://github.com/your-username/orb.git
cd orb
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open `http://localhost:5000` to begin scrying.

## The Experience

Two mystical interfaces:
- **Pondering** (`/orb`) - Touch the orb to receive visions from the void
- **Creating prophecies** (`/input`) - Inscribe your essence through words or drawings

## Project Structure

```
orb/
├── app.py              # Flask app + API routes
├── database.py         # SQLite functions  
├── templates/          # HTML interfaces
├── static/uploads/     # User drawings
└── instance/orb.db    # Database
```

## Core Features

- **Anonymous Sharing**: No accounts, pure mystical exchange
- **Dual Input**: Text submissions or canvas drawings
- **Random Retrieval**: True randomness for scrying experience
- **Secure Uploads**: PIL validation, UUID filenames, 5MB limit
- **Mobile Responsive**: Works across all devices

## Design Philosophy

Radical minimalism meets dark fantasy. Feels like discovering an ancient artifact rather than using a modern web app. Gothic typography, mysterious terminology, and dramatic emergence animations create a unique mystical experience.

---

Built for Bootdev Hackathon Weekend
