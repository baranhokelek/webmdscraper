# webmdscraper

Before running the scraper, create a virtual Python environment and make sure that `scrapy` module is installed.

## Setting up the virtual environment

Run the following commands:
```
python -m venv venv
```
(if you intend to use a different version of Python, replace the word `python` with your dedicated version (e.g., `python3.10`))
```
source venv/bin/activate
```

Then, install the required libraries (currently, only `scrapy`) via pip:
```
pip install -r requirements.txt
```

## Running the project

Run the following commands in order (each one generates an output file the next one depends upon, so executing them out of order won't work):

```
scrapy crawl states-spider
```
This one generates the urls for individual states in a text file.
```
scrapy crawl city-spider
```
This one generates the urls for individual cities in a text file.
```
scrapy crawl page-spider
```
This one generates the urls for individual pages ($state/$city/?pagenumber=$page) in a text file.
```
scrapy crawl doctor-spider -O $filename.json -s LOG_FILE=path/to/log/file
```
This part generates a json file that contains the following information:
1. Name: Name of the doctor
2. Specialty: Specialties of the doctor if listed
3. State: State that the doctor is operating in
4. Link: Link to the WebMD page of the doctor
5. Conditions Treated: Conditions treated by the doctor, if listed
6. Hospital Affiliations: Hospitals the doctor is affiliated with, if listed
7. Locations:
    1. Name: Name of the location
    2. Address: Address of the location
    3. Clinic Phone: Phone number of the location
    4. Website: Website of the location

(If location info is unstructured, the whole text will be retrieved in an unorderly manner)