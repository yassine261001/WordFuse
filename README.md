## Resources & Acknowledgements

This project was built with help from the following resources:

- [Corey Schafer's Django Tutorial](https://www.youtube.com/playlist?list=PL-osiE80TeTtoQCKZ03TU5fNfx2UY6U4p) — project structure, views, models
- [Django Official Documentation](https://docs.djangoproject.com/) — URL routing, ORM, authentication
- [MDN Web Docs](https://developer.mozilla.org/) — JavaScript fetch() API and CSRF handling
- [DictionaryAPI.dev](https://dictionaryapi.dev/) — free word validation API
- Stack Overflow — various debugging and code snippets

# WordFuse

A syllable word game built with Django.

## Setup

1. Clone the repo
2. Create and activate a virtual environment:

```
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux
```

3. Install dependencies:
```
pip install -r requirements
```

4. Run migrations:
```
python manage.py migrate (python3 if python does not work)
```

5. Start the server:
```
python manage.py runserver
```

6. Open http://127.0.0.1:8000

## Test accounts
- Admin: admin / imc-admin (access /admin/)
- Normal user: user1 / imc-user

## Running tests
pytest







