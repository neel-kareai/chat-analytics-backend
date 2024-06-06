# KareAI: Analytics Agent

## Setup

1. Clone the repository:

   ```bash
   git clone <repository_url>
   ```

2. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Apply database migrations using Alembic:

   ```bash
   alembic upgrade head
   ```

4. Configure the project:

   - Create a `.env` file and set the required environment variables.

5. Start the development server:

   ```bash
   uvicorn app:app --reload
   ```
