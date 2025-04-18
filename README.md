# Melanoma Detection Analytics Dashboard

A standalone analytics dashboard for the Melanoma Detection System.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
- Copy `.env.example` to `.env`
- Update the `BASE_URL` to point to your backend server

4. Run the dashboard:
```bash
streamlit run main.py
```

## Features

- Secure login system
- Interactive date range filtering
- Overview statistics
- User activity tracking
- Risk analysis visualization
- Interactive charts and graphs