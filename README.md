## JEE Problem extractor

Extracts the question-answer pairs from JEE Advanced papers.

### Running Instructions

Ensure you have an up-to-date installation of python (my installation is 3.12.9)

Install `pymupdf` and `pillow`:

```
pip install pymupdf
pip install pillow
```

Create folder `output` (this is where the images will go)

Run program using the following commend:

```
python main.py [path to pdf]
```

Images and JSON output will be in the output directory

### Explanation

The code itself is currently slightly messy but the main pipeline is as so:

-   The PDF is read page-by-page
-   First the page goes through a preprocessing step where the text blocks and images are put into a reading order
    -   The blocks are then put together into one full string (the images are saved and text references to the images are put in instead)
-   The program then extracts all of the answers from the page (since they will appear in the same order as the question they refer to but may not appear exactly under the question)
-   The program then splits the page apart based on the questions and throws the top part away, since it is header and instruction information
-   The program also does a check to ensure the number of answers on page are the same as the number of questions
-   The program then goes through each question and determines which type of question it is
    -   If it is multiple choice, then it will find the start of the answer section, extract all the options, and then find the correct ones based on the written answer
    -   If it is a free response question, then it will simply use the answer written in the key
-   The program was also planned to do a bit of processing to the question and answer text (seen by `parse_pdf_content`) but that was not able to be handled within the timeframe

### Faults & How to improve them

-   There are a few bugs with images
    -   Images may appear out of order
        -   This can be fixed by improving the block ordering in the first step
    -   Images appear to be exported incorrectly
        -   ~~This requires a bit more digging into the PyMuPDF documentation in order to understand exactly where the problem is~~
        -   After more investigation, it appears that the only way to do this is to create an image by rendering only that section of the PDF
            -   I have implemented this solution
    -   Math does not show up properly
        -   A solution I was thinking of was to pass along information about the bounding boxes of each text block during the preprocessing step. Then, inside `parse_pdf_content` the bounding box of the text could be calculated and PyMuPDF could be used to create an image of the text. This would then be sent to a LLM (such as ChatGPT or Gemini), which would then output the LaTeX for the math.
