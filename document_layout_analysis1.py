import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from collections import Counter

def classify_pdf_fonts(raw_font_sizes):
    """
    Takes a raw list of font sizes (extracted from XML), cleans noise,
    clusters them using K-Means, and assigns semantic roles (Body, Header, Footer).
    
    Args:
        raw_font_sizes (list): A list of floats, e.g., [12.0, 12.1, 14.0, 12.0]
        
    Returns:
        dict: A mapping of {font_size: 'Role Name'}, e.g., {12.0: 'Body Text'}
    """
    
    if not raw_font_sizes:
        return {}

    # --- PHASE 1: NOISE REDUCTION ---
    # PDF generation often results in floating point errors (e.g., 11.98 vs 12.0).
    # We round to the nearest 0.5 to standardize them.
    cleaned_sizes = [round(x * 2) / 2 for x in raw_font_sizes]
    
    # Count frequency: How often does each font appear in the text?
    # This is crucial: The font with the highest count is almost always "Body Text".
    size_counts = Counter(cleaned_sizes)
    
    # Get unique sizes for clustering
    unique_sizes = np.array(sorted(size_counts.keys())).reshape(-1, 1)
    
    # --- PHASE 2: HANDLING EDGE CASES ---
    # If document has very few font types (< 3), K-Means isn't needed.
    # We just sort them by size.
    if len(unique_sizes) < 3:
        # Simple heuristic: Largest is Header, Most Frequent is Body
        most_frequent = max(size_counts, key=size_counts.get)
        results = {}
        for size in unique_sizes.flatten():
            if size == most_frequent:
                results[size] = "Body Text"
            elif size > most_frequent:
                results[size] = "Header"
            else:
                results[size] = "Footer/Meta"
        return results

    # --- PHASE 3: UNSUPERVISED CLUSTERING (K-Means) ---
    # We test K (number of clusters) from 2 up to 6 to find the best fit.
    best_k = 2
    best_score = -1
    best_model = None
    
    # Don't try more clusters than we have unique fonts
    max_k = min(6, len(unique_sizes))
    
    for k in range(2, max_k):
        # n_init=10 runs the algo 10 times to find best starting points
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(unique_sizes)
        
        # Silhouette score tells us how well separated the groups are
        score = silhouette_score(unique_sizes, labels)
        
        if score > best_score:
            best_score = score
            best_k = k
            best_model = kmeans
            best_labels = labels

    # --- PHASE 4: SEMANTIC LABELING ---
    # 1. Group unique fonts by their cluster ID
    clusters = {} 
    for size, label in zip(unique_sizes.flatten(), best_labels):
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(size)
        
    # 2. Analyze each cluster to find "Body Text"
    cluster_stats = []
    for cid, sizes in clusters.items():
        # Total occurrences of ALL fonts in this cluster
        total_volume = sum(size_counts[s] for s in sizes)
        # Average font size of this cluster
        avg_size = sum(sizes) / len(sizes)
        
        cluster_stats.append({
            "sizes": sizes,
            "volume": total_volume,
            "avg_size": avg_size
        })

    # The cluster with the HIGHEST VOLUME (most text) is Body Text
    body_cluster = max(cluster_stats, key=lambda x: x["volume"])
    
    # Sort clusters by size (Small -> Large) to determine hierarchy
    cluster_stats.sort(key=lambda x: x["avg_size"])
    
    # Find the index of the body cluster in the sorted list
    # Because we sorted by size, objects are now memory-distinct, so we match by average size
    body_index = -1
    for i, stats in enumerate(cluster_stats):
        if stats["avg_size"] == body_cluster["avg_size"]:
            body_index = i
            break
            
    # 3. Assign Final Roles
    final_mapping = {}
    
    for i, stats in enumerate(cluster_stats):
        role = "Unknown"
        
        if i < body_index:
            role = "Footer / Meta"
        elif i == body_index:
            role = "Body Text"
        else:
            # Header Tier 1 is immediately above body, Tier 2 is larger, etc.
            tier = i - body_index
            role = f"Header (Tier {tier})"
            
        # Map every specific float size in this cluster to this Role
        for size in stats["sizes"]:
            final_mapping[size] = role
            
    return final_mapping

# ==========================================
# INTEGRETATION EXAMPLE
# ==========================================

# 1. Assume this is the list we got from your XML extractor
# (Simulating the data from your image: 15s are body, 27 is Title, 21 is H2)
xml_extracted_sizes = (
    [27.0] * 5 +              # Main Titles "Certificate of Coverage"
    [21.0] * 20 +             # Sub headers
    [15.0, 15.1, 14.9] * 500 + # Body Text (Massive amount)
    [11.0] * 50               # Footers
)

# 2. Run classification
font_role_map = classify_pdf_fonts(xml_extracted_sizes)

# 3. View Results
print(f"{'Font Size':<10} | {'Assigned Role'}")
print("-" * 30)
for size in sorted(font_role_map.keys()):
    print(f"{size:<10} | {font_role_map[size]}")