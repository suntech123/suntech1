def get_adi_results_optimized(file_path: str):
    d = get_form_recognizer_read_result(file_path, "prebuilt-layout")
    
    page_numbers_y_coords = {}
    tables_y_coords = {}
    INCH_TO_POINT = 72

    # 1. Page Numbers (Same as above)
    for p in d.get('paragraphs', []):
        if p.get('role') == 'pageNumber':
            region = p['boundingRegions'][0]
            # Use slicing [1::2] to get every 2nd element starting at index 1 (the Ys)
            page_numbers_y_coords[region['pageNumber']] = min(region['polygon'][1::2]) * INCH_TO_POINT

    # 2. Tables (Direct Bounding Box Access)
    for table in d.get('tables', []):
        # Most modern Azure results provide the bounding region for the whole table
        if 'boundingRegions' in table:
            for region in table['boundingRegions']:
                page_num = region['pageNumber']
                y_coords = region['polygon'][1::2]
                
                t_min = min(y_coords) * INCH_TO_POINT
                t_max = max(y_coords) * INCH_TO_POINT
                
                if page_num in tables_y_coords:
                    # Expand existing box to include this new table
                    tables_y_coords[page_num][0] = min(tables_y_coords[page_num][0], t_min)
                    tables_y_coords[page_num][1] = max(tables_y_coords[page_num][1], t_max)
                else:
                    tables_y_coords[page_num] = [t_min, t_max]
        
        # Fallback: If 'boundingRegions' is missing on the table object, use the cell logic here
        else:
            # Insert the cell iteration logic from Approach A here
            pass

    return page_numbers_y_coords, tables_y_coords