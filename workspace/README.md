# Nature Quest Backend

## Quick Start

1. **Clone the repository:**
   ```sh
   git clone <repo-url>
   cd nature-quest/workspace
   ```
2. **Create and configure your environment:**
   - Copy `.env.example` to `.env` and update values as needed.
   - (Optional) Create a virtual environment and activate it.
3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
4. **Run migrations:**
   ```sh
   python manage.py migrate
   ```
5. **Run the server:**
   ```sh
   python manage.py runserver
   ```
6. **Check health endpoint:**
   - Visit [http://localhost:8000/health](http://localhost:8000/health) — should return HTTP 200.

## Seeding Data
- Add your seed scripts or fixtures in the `backend` app or provide instructions here.

## Demo
See `DEMO.md` for demo instructions.
