# CampusConnect — Smart Campus Companion

A beginner-friendly responsive college project built with Python Flask, SQLite, HTML and CSS.

## Features
- Responsive dashboard for desktop and mobile
- Campus notices, events, and lost-and-found posts
- Search and category filters
- Create and delete posts
- SQLite database persists posts
- Sample posts added automatically on first run

## Requirements
- Python 3.10 or newer
- Internet is only needed to load the optional Google Fonts; the app itself works without them.

## Run on Windows
1. Extract the ZIP file.
2. Open the extracted `campusconnect` folder.
3. Click the address bar in File Explorer, type `cmd`, and press Enter.
4. Run:

   ```bash
   py -m venv .venv
   .venv\Scripts\activate
   py -m pip install -r requirements.txt
   py app.py
   ```

5. Open `http://127.0.0.1:5000` in your browser.

If `py` is not recognized, try `python` instead.

## Run on macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```
Then open `http://127.0.0.1:5000`.

## Test checklist
- Add a Notice, Event, and Lost & Found post.
- Search for a word in a post title or description.
- Filter by category.
- Delete a post.
- Stop and restart the server and confirm that remaining posts persist.

## Demo on a phone using the same Wi-Fi
1. Connect the laptop and phone to the same trusted Wi-Fi.
2. Find the laptop's local IPv4 address by running `ipconfig` in Command Prompt.
3. Keep the Flask app running. On your phone, open `http://LAPTOP-IP:5000` (replace `LAPTOP-IP` with the laptop's IPv4 address).
4. If Windows Firewall asks, only allow access on a trusted private network.

Do not expose Flask's development server directly to the public internet. For a public demo, deploy behind a production WSGI server.

## College presentation outline
1. Problem: campus notices and lost items are scattered across different channels.
2. Solution: one responsive campus board.
3. Technologies: Python, Flask, SQLite, HTML, CSS.
4. Demo: create a post, search, filter, delete, and refresh to show persistence.
5. Future scope: student/admin login, image uploads, moderation, email notifications, and QR codes.

## Important
This is a college-project prototype. It has no login or role-based access yet, so anyone who can access it can create or delete posts. Use fictional/sample data for classroom demos.
