import time
import pickle
import requests
from flask import Flask, render_template, request
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException

# Initialize Flask app
app = Flask(__name__)

# Load the movie list and similarity matrix
with open('artifacts/movie_list.pkl', 'rb') as f:
    movies = pickle.load(f)

with open('artifacts/similarity.pkl', 'rb') as f:
    similarity = pickle.load(f)

# Set up retries
session = requests.Session()
adapter = HTTPAdapter(max_retries=3)  # Max retries set to 3
session.mount('https://', adapter)
session.mount('http://', adapter)

# Function to fetch movie details (with retries and error handling)
def fetch_movie_details(movie_id, retries=3):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=8265bd1679663a7ea12ac168da84d2e8&language=en-US"
    try:
        response = session.get(url)
        response.raise_for_status()  # Will raise an error for 4xx/5xx responses
        data = response.json()

        title = data.get('title')
        overview = data.get('overview', 'No overview available.')
        release_date = data.get('release_date', 'N/A')
        poster_path = data.get('poster_path')

        return {
            'title': title,
            'overview': overview,
            'release_date': release_date,
            'poster': f"https://image.tmdb.org/t/p/w500/{poster_path}" if poster_path else None
        }
    except RequestException as e:
        print(f"Error fetching movie details for movie ID {movie_id}: {e}")
        if retries > 0:
            time.sleep(2)  # Wait for 2 seconds before retrying
            return fetch_movie_details(movie_id, retries-1)  # Retry with one less retry count
        else:
            return {
                'title': 'Unknown',
                'overview': 'Error fetching details.',
                'release_date': 'N/A',
                'poster': None
            }

# Function to get movie recommendations
def recommend(movie_name):
    # Find the movie by its title
    movie = movies[movies['title'] == movie_name].iloc[0]
    movie_id = movie['id']  # Ensure using the correct column name
    idx = movies[movies['title'] == movie_name].index[0]
    distances = sorted(list(enumerate(similarity[idx])), reverse=True, key=lambda x: x[1])

    recommended_movies = []
    for i in distances[1:6]:  # Get top 5 recommendations (skip the first one as it’s the selected movie itself)
        movie_info = movies.iloc[i[0]]
        movie_details = fetch_movie_details(movie_info['id'])  # Fetch movie details using the updated function
        recommended_movies.append({
            'title': movie_details['title'],
            'overview': movie_details['overview'],
            'release_date': movie_details['release_date'],
            'poster': movie_details['poster']  # Use poster from movie details
        })

    return recommended_movies

# Home route for handling search and movie recommendation
@app.route('/', methods=['GET', 'POST'])
def index():
    recommended_movies = []
    selected_movie = None
    search_query = ""

    # If the form is submitted with a movie selection
    if request.method == 'POST':
        selected_movie = request.form['movie']
        recommended_movies = recommend(selected_movie)

    # Handle search query and filter movies based on search
    if request.args.get('search'):
        search_query = request.args.get('search')
        movies_filtered = movies[movies['title'].str.contains(search_query, case=False, na=False)]
    else:
        movies_filtered = movies

    return render_template('index.html',
                           movie_list=movies_filtered['title'].values,
                           recommended_movies=recommended_movies,
                           selected_movie=selected_movie,
                           search_query=search_query)


if __name__ == '__main__':
    app.run(debug=True)
