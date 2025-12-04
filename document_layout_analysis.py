import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from collections import Counter

def classify_pdf_fonts(raw_font_sizes):
    """
    Groups a noisy list of PDF font sizes into semantic clusters 
    (Body, Header, Footer) using Hybrid Statistical Clustering.
    """
    
    # --- PHASE 1: NOISE REDUCTION (Method 1) ---
    # Round to nearest 0.5 to fix floating point errors (11.98 -> 12.0)
    cleaned_sizes = [round(x * 2) / 2 for x in raw_font_sizes]
    
    # Get frequency counts (Crucial for identifying Body Text later)
    size_counts = Counter(cleaned_sizes)
    
    # Get unique sizes and reshape for Sklearn
    unique_sizes = np.array(sorted(size_counts.keys())).reshape(-1, 1)
    
    # Edge Case: If document has fewer than 3 font types, return simple mapping
    if len(unique_sizes) < 3:
        return {size: f"Group {size}" for size in unique_sizes.flatten()}

    # --- PHASE 2: UNSUPERVISED CLUSTERING (Method 4) ---
    # Find the optimal number of clusters (K) using Silhouette Score
    best_k = 2
    best_score = -1
    best_model = None
    
    # We test K from 2 up to 6 (Documents rarely have >6 distinct hierarchy levels)
    max_k = min(7, len(unique_sizes))
    
    for k in range(2, max_k):
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(unique_sizes)
        
        score = silhouette_score(unique_sizes, labels)
        
        # We prefer a lower K if scores are similar to avoid over-segmentation
        if score > best_score:
            best_score = score
            best_k = k
            best_model = kmeans

    # Get the final labels for our unique sizes
    final_labels = best_model.predict(unique_sizes)
    
    # --- PHASE 3: SEMANTIC LABELING ---
    # Group the unique sizes into their clusters
    clusters = {} # {cluster_id: [size 12.0, size 12.5]}
    for size, label in zip(unique_sizes.flatten(), final_labels):
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(size)
        
    # Calculate the Total Frequency of text in each cluster
    # This tells us which cluster is the "Body Text" (Highest Frequency)
    cluster_stats = []
    for cid, sizes in clusters.items():
        total_count = sum(size_counts[s] for s in sizes)
        avg_size = sum(sizes) / len(sizes)
        cluster_stats.append({
            "cluster_id": cid,
            "sizes": sorted(sizes),
            "total_count": total_count,
            "avg_size": avg_size
        })

    # Sort clusters by Average Font Size (Smallest -> Largest)
    cluster_stats.sort(key=lambda x: x["avg_size"])
    
    # Identify Body Text: The cluster with the highest total_count
    body_cluster = max(cluster_stats, key=lambda x: x["total_count"])
    body_index = cluster_stats.index(body_cluster)
    
    # Assign semantic names
    final_groups = {}
    
    for i, stats in enumerate(cluster_stats):
        group_name = "Unknown"
        
        if i < body_index:
            group_name = "Footer/Meta"
        elif i == body_index:
            group_name = "Body Text"
        else:
            # How many levels above body text is this?
            header_level = i - body_index
            # PDF H1 is usually the Largest, so we reverse logical order if needed
            # But here we just name them by size tier
            group_name = f"Header (Tier {header_level})"
            
        # Store result for every font size in this cluster
        for size in stats["sizes"]:
            final_groups[size] = {
                "role": group_name,
                "cluster_avg": round(stats["avg_size"], 1)
            }
            
    return final_groups

# ==========================================
# TEST RUN
# ==========================================
# Noisy Data:
# - Footnotes: ~9pt
# - Body: ~12pt (Most frequent)
# - Subheader: ~14pt
# - Title: ~24pt
raw_data = (
    [8.9, 9.0, 9.1] * 50 +              # Footnotes
    [11.9, 12.0, 12.1, 11.95] * 1000 +  # Body Text (Massive count)
    [13.9, 14.0, 14.2] * 50 +           # H2 Headers
    [23.9, 24.0, 24.1] * 10             # Main Titles
)

results = classify_pdf_fonts(raw_data)

# Print Output in a readable way
print(f"{'Font Size':<12} | {'Detected Role':<20} | {'Cluster Group'}")
print("-" * 50)
for size in sorted(results.keys()):
    info = results[size]
    print(f"{size:<12} | {info['role']:<20} | {info['cluster_avg']}")