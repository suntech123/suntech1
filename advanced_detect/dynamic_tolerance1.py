import statistics

def calculate_dynamic_tolerances(lines: list['VisualLine']) -> dict:
    if not lines:
        return {'intersect': 3.0, 'cluster': 3.0}

    # 1. Filter: Ignore noise (<0.1) and massive banners (>10.0)
    # This prevents page borders from skewing the median.
    valid_thicknesses = [l.thickness for l in lines if 0.1 < l.thickness < 10.0]
    
    if not valid_thicknesses:
        base_thickness = 1.0
    else:
        base_thickness = statistics.median(valid_thicknesses)

    # 2. Intersection Tolerance (Used for Connection Checks)
    # Rule: SAFETY FLOOR of 3.0 pixels. 
    # This ensures that even if lines are 2px apart due to bad PDF formatting, 
    # we count them as connected.
    intersect_tol = max(3.0, base_thickness * 1.5)

    # 3. Cluster Tolerance (Used for Row Counting fallback)
    # Rule: Rows need breathing room.
    cluster_tol = max(3.0, base_thickness * 2.0)

    return {
        'intersect': intersect_tol,
        'cluster': cluster_tol
    }