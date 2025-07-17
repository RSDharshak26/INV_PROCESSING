import re

val = "prices \n 500 \n 200.00 \n 620.90 \n hello world "


pattern = r'\d+\.?\d+'  # this matches all digits
matches = re.findall(pattern, val)  # returns list of all matches

me = re.search(pattern, val)

print("matched object is : ", matches)
# if (re.search(pattern, val)):
#         print("matched")