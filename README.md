## Generally
The script is created to parse all offenders from the site https://www.iowasexoffender.gov/ and obtain all possible data about them. All objects are saved to the database.


## Setup Database
If you want to see a structure of the database, you can see it in the file `offenders.py` (Path - `database/models/offenders.py`).

If you want to use Sqlite3.db, you don't need to do anything; just run the script. If you want to use a different database URL, you need to change the database settings in the file `settings.py` (Path - `database/settings.py`).

To set up a `PostgreSQL` database, you need to create a database and, in the settings.py file, change the database URL to your own.

Example URL for PostgreSQL: `asyncpg://postgres:pass@db.host:5432/somedb`

Example URL for SQLite (auto-create): `sqlite://database/db.sqlite3`

If you have any questions, you can refer to this documentation: `https://tortoise.github.io/databases.html#db-url`


## Config (settings.yaml)
1. `two_captcha_api_key` - API key for the service `https://2captcha.com`.
To get the api key, you need to register on the site `https://2captcha.com`, top up your balance with at least 1 dollar and get the api key in your account. 

Then you need to change the api key in the file `settings.yaml` (Path - `source folder`).
Replace the value of the `two_captcha_api_key` variable with your own.

Be careful! Every 10-18 requests the site issues a captcha. At the time of publication, to complete the full cycle of criminals, it was necessary to solve 550-600 captchas ($0.5-0.6).


## Installation
1. Install Python 3.10 or higher. (`https://www.python.org/downloads/`)
2. Open the terminal and go to the folder with the script. (`cd "path/to/folder"`)
3. Create a venv: `python3 -m venv .venv`
4. Activate venv: `.venv\bin\activate`
3. Install the required libraries. `pip install -r requirements.txt`
4. Setup database. (See `Setup Database`)
5. Setup config. (See `Config (settings.yaml)`)
6. Run the script: `python3 run.py`

