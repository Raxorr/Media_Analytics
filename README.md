# Media Analytics Dashboard

This project is a Streamlit-based web application that aggregates trending movie and TV data using the TMDB and OMDB APIs. It provides a unified view of popularity trends, ratings, streaming availability, metadata, and visual insights. The dashboard supports both dark and light themes, includes configurable filters, and is fully containerized using Docker.

Live demo: [*Add your Streamlit Cloud link here*](https://mediaanalytics-4xa4fxxeqhajnetj6swkgs.streamlit.app/)

---

## Features

- Trending movies and shows for Today or This Week  
- Detailed table including popularity, vote counts, release dates, and ratings  
- IMDb rating lookup using OMDB API  
- Streaming availability from TMDB Watch Providers  
- Popularity leaderboard using Altair charts  
- Light and dark mode  
- Adjustable number of displayed titles  
- Async API calls for improved performance  
- Dockerized for consistent deployment  
- `.env`-based secure API key management  

---

## Tech Stack

- Python 3.10+  
- Streamlit  
- TMDB API  
- OMDB API  
- aiohttp (async requests)  
- Altair  
- Docker  

---

## Project Structure

```
media-analytics/
│
├── app_streamlit.py
├── etl_fetch.py
├── run_fetch_all.py
│
├── providers/
│   ├── tmdb.py
│   ├── omdb.py
│   └── http_client.py
│
├── utils/
│   └── perf_log.py
│
├── data/
│
├── Dockerfile
├── entrypoint.sh
├── requirements.txt
└── README.md
```

---

## Setup Instructions

### 1. Clone the repository

```
git clone https://github.com/<your-username>/Media_Analytics.git
cd Media_Analytics
```

### 2. Add your `.env` file

Create a `.env` file in the project root:

```
TMDB_API_KEY=your_tmdb_key
OMDB_API_KEY=your_omdb_key
```

### 3. Install dependencies

```
pip install -r requirements.txt
```

### 4. Fetch data once

```
python run_fetch_all.py
```

### 5. Launch the Streamlit app

```
streamlit run app_streamlit.py
```

Your app will be available at:

```
http://localhost:8501
```

---

## Running with Docker

### Build the Docker image

```
docker build -t media-analytics:latest .
```

### Run the container

```
docker run -p 8501:8501 --env-file .env media-analytics:latest
```

---

## Deployment Options

This project can be deployed on:

- **Streamlit Cloud**  
- **Railway (Docker)**  
- **Render (Docker)**  
- **Fly.io**  
- Any Docker-compatible hosting environment  

---

## API Usage Notes

### TMDB Limitations
- 40 requests every 10 seconds  
- Daily limit based on account tier  
- Free tier is generous but should not be abused  

### OMDB Limitations
- 1,000 requests per day on the free tier  
- Higher limits require a paid plan  

The application batches and caches results to stay within safe limits.

---

## Attribution

Data and images are provided by The Movie Database (TMDB).  
This product uses the TMDB API but is not endorsed or certified by TMDB.

---

## License

This project is intended for educational and personal portfolio use.  
Please ensure compliance with TMDB and OMDB terms of service when using API keys.
