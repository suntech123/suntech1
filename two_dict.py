dict1 = {
    'folder_A': [1, 2, 3, 4, 5],
    'folder_B': [10, 20, 30, 40]
}

dict2 = {
    'folder_A': [4, 5, 6, 7, 8],
    'folder_B': [30, 40, 50, 60]
}

# The Solution: Dictionary Comprehension + Set Intersection (& operator)
dict3 = {k: list(set(dict1[k]) & set(dict2[k])) for k in dict1}

print(dict3)