# magus
Sophisticated name generation API

# AI Name Generator MVP

A simple FastAPI-based name generator that serves random names from pre-populated lists. This is the minimum viable product (MVP) version that can be expanded into a more sophisticated AI-powered system.

## Features

- **Multiple Cultures**: Generic, Elvish, and Norse name collections
- **Gender Support**: Male, female, and unisex names where available  
- **Batch Generation**: Generate multiple names in a single request
- **RESTful API**: Clean, documented API endpoints
- **Input Validation**: Proper error handling and request validation
- **Interactive Documentation**: Auto-generated API docs with FastAPI

## Quick Start

### 1. Setup
```bash
# Clone/download the project files
# Make sure you have Python 3.8+ installed

# Run the setup script
python setup.py
```

### 2. Start the Server
```bash
# Option 1: Use the generated run script
./run.sh        # Linux/Mac
run.bat         # Windows

# Option 2: Manual start
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
python main.py
```

### 3. Test the API
```bash
# In another terminal
python test_api.py

# Or visit the interactive docs
# http://localhost:8000/docs
```

## API Endpoints

### Generate Names
**POST** `/generate`

Generate one or more names based on specified criteria.

**Request Body:**
```json
{
  "culture": "generic",    // optional: "generic", "elvish", "norse"
  "gender": "female",      // optional: "male", "female", "unisex"
  "count": 3              // optional: 1-50, default 1
}
```

**Response:**
```json
{
  "names": [
    {
      "name": "Isabella",
      "culture": "generic",
      "gender": "female"
    }
  ],
  "total_count": 1
}
```

### Get Available Cultures
**GET** `/cultures`

Returns all available cultures and their supported genders.

### Health Check
**GET** `/health`

Simple health check endpoint.

## File Structure

```
├── main.py           # Main FastAPI application
├── requirements.txt  # Python dependencies
├── setup.py         # Setup script
├── test_api.py      # API testing script
├── run.sh/run.bat   # Generated startup scripts
└── README.md        # This file
```

## Current Name Database

- **Generic**: 10 male, 10 female, 10 unisex names
- **Elvish**: 10 male, 10 female names  
- **Norse**: 10 male, 10 female names

## Future Enhancements

This MVP can be extended with:

1. **Database Integration**: Replace in-memory lists with SQLite/PostgreSQL
2. **More Cultures**: Add Celtic, Japanese, African, etc.
3. **Name Meanings**: Add etymology and meaning data
4. **Phonetic Processing**: Add pronunciation guides
5. **AI Generation**: Implement the full neural name generation system
6. **User Preferences**: Add user accounts and preference learning
7. **Batch Import**: Tools to import large name datasets

## Development

### Adding New Names
Edit the `NAMES_DB` dictionary in `main.py`:

```python
NAMES_DB = {
    "new_culture": {
        "male": ["Name1", "Name2", ...],
        "female": ["Name3", "Name4", ...]
    }
}
```

### Running Tests
```bash
# Start the server first
python main.py

# Then run tests in another terminal
python test_api.py
```

### API Documentation
When the server is running, visit:
- **Interactive docs**: http://localhost:8000/docs
- **Alternative docs**: http://localhost:8000/redoc

## Dependencies

- **FastAPI**: Modern, fast web framework for building APIs
- **Uvicorn**: ASGI server for running FastAPI
- **Pydantic**: Data validation using Python type annotations

## License

This is a learning/development project. Adapt and modify as needed for your use case.

## Contributing

This MVP is designed to be simple and extensible. Feel free to:
- Add more name collections
- Implement additional validation
- Enhance the response format
- Add new cultures or features

The codebase is structured to make it easy to integrate with the more advanced AI name generation system described in the project documentation.