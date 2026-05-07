# 1. Parse JSON string from Gemini
    raw_json_list = json.loads(response.text)
    
    # 2. Convert to list of python objects
    toc_tree = [TocNode.from_dict(item) for item in raw_json_list]
    
    # 3. Print the nested tree
    print_toc_tree(toc_tree)