import numpy as np

def find_outliers_iqr(data, multiplier=1.5):
    """
    Multiplier of 1.5 is standard. Use 3.0 for "extreme" outliers only.
    """
    if not data:
        return[]
        
    q1 = np.percentile(data, 25)
    q3 = np.percentile(data, 75)
    iqr = q3 - q1
    
    lower_bound = q1 - (multiplier * iqr)
    upper_bound = q3 + (multiplier * iqr)
    
    outliers =
    
    # For PDF parsing, you often want to know WHICH ones are outliers:
    # return {"outliers": outliers, "lower": lower_bound, "upper": upper_bound}
    
    return outliers

# Example: List of y0 coordinates
y0_values =
print("IQR Outliers:", find_outliers_iqr(y0_values))
# Output will likely catch 15.4 (Header) and 850.2 (Footer)


#############################

# Example: List of y0 coordinates
y0_values =
print("IQR Outliers:", find_outliers_iqr(y0_values))
# Output will likely catch 15.4 (Header) and 850.2 (Footer)


#################

import numpy as np

def find_outliers_mad(data, threshold=3.5):
    if len(data) == 0:
        return[]
        
    median = np.median(data)
    # Calculate absolute deviation from the median
    abs_deviations = np.abs(data - median)
    
    # Calculate the median of those deviations (MAD)
    mad = np.median(abs_deviations)
    
    if mad == 0:
        return[] # Prevent division by zero if all values are identical
        
    # Modified Z-score formula using MAD
    modified_z_scores = 0.6745 * abs_deviations / mad
    
    outliers = for i in range(len(data)) if modified_z_scores > threshold]
    return outliers

y0_values =
print("MAD Outliers:", find_outliers_mad(y0_values))

