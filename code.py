import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
import umap
import hdbscan
from sklearn.neighbors import NearestCentroid # A simple way to predict based on centroids
from sklearn.metrics.pairwise import cosine_similarity # Or euclidean_distances

# --- Configuration ---
MODEL_NAME = 'all-MiniLM-L6-v2' # Good balance of speed and quality
UMAP_N_COMPONENTS = 50       # Reduce to 50 dimensions (adjust based on data complexity)
UMAP_RANDOM_STATE = 42
HDBSCAN_MIN_CLUSTER_SIZE = 15 # Minimum number of samples in a cluster (tune this!)
HDBSCAN_MIN_SAMPLES = 5      # Number of samples in a neighborhood for a point to be considered as a core point (tune!)

# --- 1. Simulate Data (Replace with your 200k paragraphs) ---
# Using a smaller dataset for a runnable example
paragraphs = [
    "The cat sat on the mat.",
    "A feline rested on the rug.",
    "Dogs bark loudly at strangers.",
    "Canine companions make noise.",
    "The quick brown fox jumps over the lazy dog.",
    "Artificial intelligence is transforming industries.",
    "Machine learning algorithms are key to modern AI.",
    "Deep learning models require vast amounts of data.",
    "Renewable energy sources like solar and wind are growing.",
    "Sustainable practices are important for the environment.",
    "Climate change mitigation efforts are crucial globally.",
    "Coding in Python is fun and productive.",
    "Java is a widely used programming language.",
    "JavaScript is essential for web development.",
    "Databases store and manage information.",
    "SQL is used to query relational databases.",
    "NoSQL databases offer flexibility.",
    # Adding more to make clustering more meaningful
    "Scientists discovered a new exoplanet.",
    "Astronomers observed a distant galaxy.",
    "Space exploration advancements continue.",
    "Cooking involves preparing food with heat.",
    "Baking uses dry heat to cook dough or batter.",
    "Grilling imparts smoky flavors.",
    "Traveling allows you to see new places.",
    "Tourism boosts local economies.",
    "Backpacking is a form of low-cost travel.",
] * 100 # Multiply to simulate a larger dataset (26 * 100 = 2600 paragraphs)

print(f"Simulated {len(paragraphs)} paragraphs.")

# --- 2. Generate Semantic Embeddings ---
print(f"Loading Sentence Transformer model: {MODEL_NAME}")
model = SentenceTransformer(MODEL_NAME)

print("Generating embeddings...")
# The encode method handles batching internally, but for very large datasets
# you might need to manage batching manually to control memory usage.
# For 200k, the default batching should likely be fine on a machine with decent RAM.
embeddings = model.encode(paragraphs, show_progress_bar=True)

print(f"Embeddings shape: {embeddings.shape}") # Shape: (num_paragraphs, embedding_dim)

# --- 3. Reduce Dimensionality with UMAP ---
print(f"Reducing dimensionality with UMAP to {UMAP_N_COMPONENTS} components...")
umap_reducer = umap.UMAP(n_components=UMAP_N_COMPONENTS, random_state=UMAP_RANDOM_STATE)
reduced_embeddings = umap_reducer.fit_transform(embeddings)

print(f"Reduced embeddings shape: {reduced_embeddings.shape}") # Shape: (num_paragraphs, UMAP_N_COMPONENTS)

# --- 4. Cluster with HDBSCAN ---
print("Clustering with HDBSCAN...")
# Use 'euclidean' metric which is standard for UMAP output
hdbscan_clusterer = hdbscan.HDBSCAN(
    min_cluster_size=HDBSCAN_MIN_CLUSTER_SIZE,
    min_samples=HDBSCAN_MIN_SAMPLES,
    metric='euclidean'
)
cluster_labels = hdbscan_clusterer.fit_predict(reduced_embeddings)

# --- 5. Analyze Clustering Results ---
df = pd.DataFrame({'paragraph': paragraphs, 'cluster_label': cluster_labels})

n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
n_noise = list(cluster_labels).count(-1)

print(f"\nHDBSCAN found {n_clusters} clusters.")
print(f"{n_noise} paragraphs were labeled as noise (-1).")

print("\n--- Cluster Distribution ---")
print(df['cluster_label'].value_counts().sort_index())

print("\n--- Sample Paragraphs from Clusters (excluding noise) ---")
sample_clusters = [label for label in set(cluster_labels) if label != -1]
if sample_clusters:
    # Show samples from up to 5 clusters, or all if less than 5
    for label in sorted(sample_clusters)[:min(len(sample_clusters), 5)]:
        print(f"\n--- Cluster {label} ---")
        cluster_paragraphs = df[df['cluster_label'] == label]['paragraph'].sample(min(5, len(df[df['cluster_label'] == label])))
        for i, para in enumerate(cluster_paragraphs):
            print(f"{i+1}. {para[:150]}...") # Print first 150 chars

# --- 6. Prepare for Prediction (Centroid-Based) ---
# We'll use the average embedding of points within each cluster as the cluster centroid.
# We exclude noise points (-1) from centroid calculation.
clustered_data = df[df['cluster_label'] != -1]
clustered_embeddings = reduced_embeddings[df['cluster_label'] != -1]
clustered_labels = df[df['cluster_label'] != -1]['cluster_label']

# Calculate centroids using NearestCentroid - it's designed for this
# Or calculate manually: clustered_data.groupby('cluster_label')[['embedding_cols']].mean()
if len(clustered_data) > 0:
    centroid_classifier = NearestCentroid(metric='cosine') # Use cosine similarity for centroids
    # Fit the centroid classifier on the reduced embeddings and their labels
    centroid_classifier.fit(clustered_embeddings, clustered_labels)

    print("\nPrepared centroid classifier for prediction.")

    # --- 7. Predict Cluster for a New Paragraph ---
    def predict_cluster_for_paragraph(new_paragraph: str, model: SentenceTransformer, umap_reducer: umap.UMAP, predictor: NearestCentroid):
        """
        Predicts the cluster label for a new paragraph using the trained model pipeline.
        """
        # 1. Generate embedding for the new paragraph
        new_embedding = model.encode([new_paragraph])

        # 2. Reduce dimensionality using the *fitted* UMAP reducer
        new_reduced_embedding = umap_reducer.transform(new_embedding)

        # 3. Predict the cluster using the centroid classifier
        predicted_label = predictor.predict(new_reduced_embedding)

        return predicted_label[0] # predict returns an array, take the first element

    # --- Example Prediction ---
    new_paragraph_example = "Learning about data analysis with pandas is powerful."
    if len(clustered_data) > 0:
        predicted_cluster = predict_cluster_for_paragraph(
            new_paragraph_example,
            model,
            umap_reducer,
            centroid_classifier
        )
        print(f"\nNew paragraph: '{new_paragraph_example[:100]}...'")
        print(f"Predicted cluster label: {predicted_cluster}")

        # Example 2
        new_paragraph_example_2 = "I love my pet dog."
        predicted_cluster_2 = predict_cluster_for_paragraph(
            new_paragraph_example_2,
            model,
            umap_reducer,
            centroid_classifier
        )
        print(f"\nNew paragraph: '{new_paragraph_example_2[:100]}...'")
        print(f"Predicted cluster label: {predicted_cluster_2}")

    else:
        print("\nNo clusters found (all data might be noise). Cannot perform prediction.")

else:
     print("\nNo data points assigned to clusters. Cannot train centroid classifier or predict.")
