# Generating patient reports using the GEL CIP API
This script takes a GeL participantID and queries the CIP-API to return the clinical report

## How it works
The script takes an Gel Participant ID as an input.
#### Authentication
The script authentication.py creates an access token using the username and passwords provided in the files auth_pw.txt and auth_username.txt.

Each file should just contain a single line containing the username or password.Examples of these files are provided (prefixed with dummy).
#### Reading API
Using the Python requests modules and this access token the CIP-API is accessed. Only 100 samples are returned per page so if the GEL participant ID is not found the next page is accessed.
#### Selecting which report to return
Once the Participant ID is found a few checks are performed to ensure the correct report is found.
1. If the patient status is blocked no report will be returned
2. Reports can be generated from multiple versions of the CIP version. The report is taken from the most recent version
3. There can also be multiple reports generated for each verison of the CIP. The most recent report is taken.
#### Modification of the report
The html report is downloaded into a beautiful soup object.

The report is edited to remove the GeL logo and the Gel Address from near the top of the report.

The coverage section is then modified so it is always expanded (removing the click to expand option)

The colour of the report header is modified by altering the CSS (the new colour can be specified in the __init__ function)

A new table is also inserted above the participant information table. This uses the template found in the patient_info_table_template.html.
#### Adding patient information from local LIMS system
This table is then populated by a function which queries the LIMS system. This will need to be modified between labs.

This function must essentially populate a dictionary containing one entry for each item in the patient_info_table_template.html eg patient_info_dict={"NHS":NHS,"PRU":PRU,"dob":DOB,"firstname":FName,"lastname":LName,"gender":Gender}

### output
A pdf and the intermediary html files are produced in the locations specified in the __init__ function.
These files are named GelParticipantID.pdf eg 12345678.pdf


## Requirements
This has been tested on a Linux server connected to an N3 network.

#### Python
The following Python packages are required:

	beautifulsoup4 

	jinja2 

	pyODBC 

	requests

	pdfkit ^ 

^ This must be installed via pip
 
	pip install pdfkit

#### wkhtmltopdf
This is the software used by pdfkit to convert html to pdf.

It can be installed via apt-get HOWEVER THIS VERSION CANNOT RUN IN HEADLESS  - This may however be a useful exercise to install dependancies!

	sudo apt-get install wkhtmltopdf
	
	sudo apt-get remove wkhtmltopdf

A version that can be run headless was downloaded using wget

	wget https://downloads.wkhtmltopdf.org/0.12/0.12.4/wkhtmltox-0.12.4_linux-generic-amd64.tar.xz

	tar xpvf wkhtmltox-0.12.4_linux-generic-amd64.tar.xz

Further dependancies were required:

	sudo apt-get install libxrender1 libfontconfig

## usage
python get_report.py -g 12345678
