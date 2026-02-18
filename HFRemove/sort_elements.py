####1

# Sort in-place (modifies the list directly to save memory)
# Key: 
#  1. Vertical Position (Rounded to nearest pixel to handle float jitter)
#  2. Horizontal Position (Left to Right)

all_elements.sort(key=lambda e: (round(e.rect.y0), e.rect.x0))

# Now elements[0] is the top-left-most item on the page


####2

from operator import attrgetter

# Sorts purely by top edge location
all_elements.sort(key=lambda e: e.rect.y0)

####3

# Sorts by Bottom Edge (y1), descending (largest Y first)
all_elements.sort(key=lambda e: e.rect.y1, reverse=True)

# Now elements[0] is the absolute lowest item on the page


####4 Grouping


from itertools import groupby

# 1. Sort by Y (rounded) then X
all_elements.sort(key=lambda e: (round(e.rect.y0), e.rect.x0))

# 2. Group by vertical position (simulating lines)
# This creates a structure like:
# Line 1 (y=50): [LogoElement, HospitalNameElement]
# Line 2 (y=70): [PolicyNumberElement, DateElement]

lines = []
for y_pos, line_items in groupby(all_elements, key=lambda e: round(e.rect.y0)):
    lines.append(list(line_items))

# Usage: Check the first 3 lines for header content
for line in lines[:3]:
    line_text = " ".join([elem.text for elem in line])
    print(f"Row at Y={line[0].rect.y0}: {line_text}")
