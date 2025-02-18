import pandas as pd
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Assuming you have a dataset of movies in CSV format
movies_df = pd.read_csv('tmdb_5000_movies.csv')

# Process genres into a single string (similar to the method in your Streamlit code)
def process_genres(genres):
    try:
        genres_list = eval(genres) if isinstance(genres, str) else []
        genre_names = [genre['name'] for genre in genres_list if isinstance(genre, dict)]
        return ' '.join(genre_names)
    except:
        return ''

# Apply genre processing
movies_df['genres'] = movies_df['genres'].apply(process_genres)

# TF-IDF Vectorizer to compute genre-based similarity
tfidf_vectorizer = TfidfVectorizer(stop_words='english')
tfidf_matrix = tfidf_vectorizer.fit_transform(movies_df['genres'])

# Compute cosine similarity matrix
similarity_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)

# Save the movie list and similarity matrix as pickle files
with open('artifacts/movie_list.pkl', 'wb') as f:
    pickle.dump(movies_df, f)

with open('artifacts/similarity.pkl', 'wb') as f:
    pickle.dump(similarity_matrix, f)

print("Pickle files saved successfully!")
