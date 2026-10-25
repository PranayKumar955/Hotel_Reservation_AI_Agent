# Hotel Reservation AI Agent

A college project demo built with Python, Flask, SQLite, HTML, CSS, and JavaScript.

## Features
- Hotel home page and room listings
- Date-based room availability search
- Booking form with booking reference and total cost
- Booking status lookup using reference + email
- Guest cancellation
- Chat assistant for common hotel questions (rule-based; no paid API required)
- Admin login, dashboard statistics, room creation/activation, and booking cancellation
- SQLite database created and seeded automatically on first run

## Requirements
- Python 3.10 or newer
- VS Code
- Internet connection only for optional CDN fonts/icons; the app itself runs locally

## Run in VS Code (Windows)
1. Extract the ZIP and open the `hotel_reservation_ai_agent` folder in VS Code.
2. Open Terminal → New Terminal.
3. Create a virtual environment:
   ```powershell
   py -m venv .venv
   ```
4. Activate it:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
   If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and activate again. Or use Command Prompt:
   ```bat
   .venv\Scripts\activate.bat
   ```
5. Install dependencies:
   ```powershell
   python -m pip install -r requirements.txt
   ```
6. Start the application:
   ```powershell
   python app.py
   ```
7. Open `http://127.0.0.1:5000` in your browser.

## Run on macOS/Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```
Then visit `http://127.0.0.1:5000`.

## Demo admin login
- URL: `http://127.0.0.1:5000/admin/login`
- Username: `admin`
- Password: `admin123`

**Demo credentials only. Change them before any public deployment.** You can set environment variables before running:
- Windows PowerShell:
  ```powershell
  $env:ADMIN_USERNAME="hoteladmin"
  $env:ADMIN_PASSWORD="a-long-unique-password"
  $env:SECRET_KEY="a-long-random-secret"
  python app.py
  ```
- macOS/Linux:
  ```bash
  export ADMIN_USERNAME="hoteladmin"
  export ADMIN_PASSWORD="a-long-unique-password"
  export SECRET_KEY="a-long-random-secret"
  python app.py
  ```

## Project structure
```text
hotel_reservation_ai_agent/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── .env.example
├── hotel.db                 # created automatically; ignored by Git
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── availability.html
│   ├── book.html
│   ├── confirmation.html
│   ├── booking_status.html
│   ├── admin_login.html
│   ├── admin_dashboard.html
│   └── 404.html
└── static/
    ├── css/style.css
    └── js/chat.js
```

## Test checklist for your project expo
1. Open home page and inspect sample rooms.
2. Search availability for dates in the future.
3. Book a room and note the booking reference.
4. Search booking status using the reference and the same email.
5. Ask chatbot: “What are your room prices?” and “What time is check-in?”
6. Sign in as admin, add a room, deactivate/activate a room, and cancel a booking.
7. Try searching the same room/date range again; confirmed reservations should block overlapping dates.

## Important limitations
- This is a college demonstration, not a production hotel system.
- Chatbot replies are rule-based and use the app's local room data. It is not a generative AI model yet.
- Payment gateway, email/SMS confirmation, robust role management, CSRF protection, audit logs, and production deployment hardening are not included.
- Do not store real guest data or deploy publicly with demo credentials.
- If two guests try to book simultaneously, this small demo does not provide full transactional reservation locking.

## GitHub upload
1. Create a new repository on GitHub named `hotel-reservation-ai-agent`.
2. Do not upload `hotel.db`, `.venv`, or secret credentials.
3. In VS Code terminal, from the project root:
   ```bash
   git init
   git add .
   git commit -m "Initial Hotel Reservation AI Agent project"
   git branch -M main
   git remote add origin https://github.com/YOUR-USERNAME/hotel-reservation-ai-agent.git
   git push -u origin main
   ```
4. Replace `YOUR-USERNAME` with your GitHub username.
5. Send your HOD the repository URL, e.g. `https://github.com/YOUR-USERNAME/hotel-reservation-ai-agent`.

If Git is not installed, install Git for Windows/macOS/Linux, reopen VS Code, and run the commands again.
