from pypdf import PdfReader as pdfr
import pandas as pd
import re
import math

reader = pdfr("foreclosure list.pdf")

data = ''.join([reader.pages[i].extract_text() for i in range(len(reader.pages))])

data = re.sub(r"\b\d+/44\b", "", data)

rows = data.split('\n')

cleaned_rows=[]
i=0
combined_data = set()

split_words = pd.read_excel("name_exceptions.xlsx")
while i < len(rows):

    found = False
    for inx, word1 in enumerate(split_words["line_1"]):
        if rows[i].endswith(word1.strip()):
            print("FIRST COMBINE", word1)
            word2 = split_words["line_2"].iloc[inx].strip()
            print("Word2", word2)
            if rows[i+1].startswith(word2):
                combined = rows[i] + ' ' + rows[i+1]
                merged_word = rows[i] + ' ' + word2
                combined_data.add(merged_word.encode('ascii', 'ignore').decode())
                cleaned_rows.append(combined)
                # join = True
                # if len(word2) != len(rows[i+1]):
                #     print("REMAINING")
                #     remaining = rows[i+1][len(word2):]
                #     print(remaining)
                #     cleaned_rows.append(remaining)
                #     i -= 1
                found = True
                break  # Break out of the inner loop
        if found:
            break  # Break out of the outer loop

    if found == True:
        i+=2
    # if any(rows[i].endswith(word.strip()) for word in split_words["line_1"]) and i + 1 < len(rows) and any(rows[i + 1].startswith(word.strip()) for word in split_words["line_2"]):
    #     print("JOIN", rows[i])
    # # if rows[i].endswith("JUDGMENT OF") and i + 1 < len(rows) and rows[i + 1].startswith("FORECLOSURE") \
    # #     or rows[i].endswith("ABC RENTAL") and i + 1 < len(rows) and rows[i + 1].startswith("DEVELOPMENT LLC") \
    # #     or rows[i].endswith("AZZARETTO PHILIP A EX") and i + 1 < len(rows) and rows[i + 1].startswith("AKA"):


    #     # Join the current and next arrays
    #     combined = rows[i] + " " + rows[i + 1]
    #     cleaned_rows.append(combined)
    #     i += 2  # Skip the next array as it's already merged
    else:
        cleaned_rows.append(rows[i])
        i += 1
# Strip redundant spaces and newlines after removal
# cleaned_data = re.sub(r"\s+", " ", cleaned_data).strip()

print(cleaned_rows)

def findHeader(start_i=0):
    pattern = r".*Name Cross Party Date TypeInstr# BookPageTownLegalConsiderationStatusFlag$"
    while cleaned_rows and start_i < len(cleaned_rows):
        try:
            match = re.search(pattern, cleaned_rows[start_i])
            if match:
                print("Match found:", match.group())
                print(start_i + 1)
                return start_i + 1
            else:
                print("did not match")
                print
                print(start_i)
                start_i += 1
        except Exception as e:
            print(f"Exception in findHeader: {e}")
            break  # Safely exit the loop
    return start_i  # Return the current index if no match is found

def findDate(row):
    date_match = re.search(r"\d{2}/\d{2}/\d{4}", row)
    print("find", row)
    if date_match:
        date = date_match.group()
        date_index = date_match.start()

        # Split the row into before and after the date
        before_date = row[:date_index].strip()
        after_date = row[date_match.end():].strip()
        print("dates")
        print((before_date,date,after_date))
        return (before_date,date,after_date)

def findCrossParty(data):
    if "JUDGMENT OF FORECLOSURE" in data:
        if data.startswith("JUDGMENT OF FORECLOSURE"):
            parts = data.split("JUDGMENT OF FORECLOSURE")
            name = "JUDGMENT OF FORECLOSURE"
            cross_party = parts[1]
            return (name, cross_party)
    # Split on 'JUDGMENT OF FORECLOSURE'
        else:
            parts = data.split("JUDGMENT OF FORECLOSURE")
            name = parts[0].strip() 
            return (name, "JUDGMENT OF FORECLOSURE")
    else:
        name = data.strip()  # If not found, the whole element is the name
        return (name, "")
    
def parseRemaining(after_date):
        
    if len(after_date.split(' ')) == 6:
        type, instrument, book, page, consideration, status = after_date.split(' ')

    elif len(after_date.split(' ')) == 4:
        type, inst_book, page, consideration_status = after_date.split(' ')
        instrument, book = inst_book[0:10], inst_book[10:]
        consideration, status = consideration_status[0:-2], consideration_status[-1]
    return (type, instrument, book, page, consideration, status)

def checkEndofPage(row):
    if 'about:blank' in row:
        return 1
    return 0


parsed_rows=[]
stop=False
start_i=0

def run(start_i):
    start_i = findHeader(start_i)
    curr_cleaned_rows = cleaned_rows[start_i:]
    i = 0
    while i < len(curr_cleaned_rows):  # Ensure index stays within bounds
        if checkEndofPage(curr_cleaned_rows[i]) == 0:
 
            if curr_cleaned_rows[i] in combined_data:
                print("CONDIDITON MET")
                curr_cleaned_rows[i] = curr_cleaned_rows[i] + ' ' + curr_cleaned_rows[i+1]
                del curr_cleaned_rows[i+1]
                print("NEW", curr_cleaned_rows[i] )
            try:
                before_date, date, after_date = findDate(curr_cleaned_rows[i])
                print('before_Date', before_date)
                name, cross_party = findCrossParty(before_date)
                type, instrument, book, page, consideration, status = parseRemaining(after_date)

            except Exception as e:
                print("Error parsing row:")
                print("pre col", curr_cleaned_rows[i - 1] if i > 0 else "N/A")
                print("column", curr_cleaned_rows[i])
                print("post col",  curr_cleaned_rows[i+1])
                print(combined_data)
                print("Traceback details:")
                import traceback
                traceback.print_exc()
            finally:
                i += 1
            
            parsed_row = {
                    "name": name,
                    "cross_party": cross_party,
                    "date": date,
                    "type": type,
                    "instrument": instrument,
                    "book": book,
                    "page": page,
                    "consideration": consideration,
                    "status": status
                }
            print(parsed_row)
            parsed_rows.append(parsed_row)
        else:
            break

    return start_i

for i in range(0,len(reader.pages)):
    print("RUN START", start_i)
    start_i = run(start_i)

df = pd.DataFrame(parsed_rows)
df.to_excel("forclosure.xlsx")