import fitz
import re
import io
from PIL import Image
import sys
import json

# Question format will be as such
# {
#     "question": [
#         ... text values
#     ],
#     answer: [
#         ... text values
#     ]
# }

# Where text values are a dictionary which contain a type (either text or image) and either a text value or a value which links to an image

# TODO: handle images
def parse_pdf_content(content):
    return [{"type": "text", "value": content}]



def get_sorted_blocks(page):
    blocks = page.get_text("dict")["blocks"]
    sorted_blocks = []

    for block in blocks:
        bbox = block["bbox"]
        block_entry = {
            "type": block["type"],  # 0=text, 1=image
            "bbox": bbox,
            "y": bbox[1],  # top y
            "x": bbox[0],  # left x
            "block": block
        }
        sorted_blocks.append(block_entry)

    # Sort blocks top-to-bottom, then left-to-right (y, x)
    sorted_blocks.sort(key=lambda b: (round(b["y"], 1), b["x"]))
    return sorted_blocks

# Preprocessing step to handle images
def extract_and_preprocess(page):
    blocks = get_sorted_blocks(page)

    out = ""
    identifier = 0

    for b in blocks:
        block = b['block']
        if block['type'] == 0:
            # Text block
            text = ""
            for line in block['lines']:
                for span in line['spans']:
                    text += span['text'] + " "
            out += text + "\n"
        
        elif block['type'] == 1:
            # Image block
            img = Image.open(io.BytesIO(block["image"]))
            out += f"[IMAGE: image_{identifier}.png]"
            img.save(f"output/image_{identifier}.png")
            identifier += 1
            
    return out

def extract_qa_pairs(pdf_path):
    doc = fitz.open(pdf_path)
    qa_list = []
    
    for page in doc:
        text = extract_and_preprocess(page)
        # Normalize text to only use \n
        text.replace("\r\n", "\n")
        # Grab answer values
        answer_values = [i[0] for i in re.findall(r'Answer: (.+)\n', text)]
        if len(answer_values) == 0:
            continue
        # Can safely remove the first part of the value since the header will always be at the top of the page
        question_split = re.split(r'Q\.\d+ +', text)[1:]
        if len(question_split) != len(answer_values):
            raise ValueError("Question and answer amount do not line up!")
        for i, question in enumerate(question_split):
            current_question = {
                "answer": []
            }
            # Clean up remaining parts of question by removing everything after the answer
            if (re.match(r'Answer: .+\n', question)):
                question = "\n".join(re.split(r'Answer: .+\n', question)[:-1])
                
            # Determine if the question is multiple choice
            if re.match(r'[A-D](, [A-D])*', answer_values[i]):
                # The last 8 parts are the answers (since in the reconstruction process the answers may have gotten out of order)
                parts = re.split(r"\(([A-D]\)) ", question)
                question = "(".join(parts[:-8])
                answers = parts[-8:]
                current_question["question"] = parse_pdf_content(question)
                answers_split = ["" for i in range(0, len(answers), 2)]
                for j in range(0, len(answers), 2):
                    index = ord(answers[j].strip()[0]) - 65
                    if index < 0 or index > 3:
                        raise ValueError("Something has gone wrong, value of " + str(index))
                    answers_split[index] = answers[j+1].strip()
                processed_answer_values = [ord(j.strip()) - 65 for j in answer_values[i].split(',')]
                for val in processed_answer_values:
                    if val < 0 or val > 3:
                        raise ValueError("Something has gone wrong, value of " + str(val))
                    current_question["answer"] = parse_pdf_content(answers_split[val].strip())
            else:
                if i == len(question_split) - 1:
                    question = question.split("\n\n\n")[0]
                current_question["question"] = parse_pdf_content(question)
                current_question["answer"] = parse_pdf_content(answer_values[i])
            qa_list.append(current_question)

    return qa_list

pairs = extract_qa_pairs(sys.argv[1])

for qa in pairs:
    print("Question:", qa["question"])
    print("Answer:", qa["answer"])
    print("----------------")

with open('output/out.json', "w") as f:
    f.write(json.dumps(pairs))