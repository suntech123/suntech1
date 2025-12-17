def detect_structure_or_image(self) -> str:
        # 1. XML Check (Tagged PDF)
        if "<Table" in self.xml or "<TR" in self.xml:
            return "TAGGED_TABLE"
            
        # 2. Image Check
        images = self.page.get_image_info()
        for img in images:
            bbox = img['bbox']
            area = (bbox[2]-bbox[0]) * (bbox[3]-bbox[1])
            page_area = self.width * self.height
            
            # If a single image takes up > 15% of page, it might be a scanned table
            if (area / page_area) > 0.15:
                return "IMAGE_TABLE"
                
        return "NONE"