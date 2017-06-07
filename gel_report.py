'''
gel_report.py
This script takes a GEL Participant ID and queries the CIP-API to return a clinical report.

This report is then modified to make it clear that this report has not been issued by GEL, including extracting some information from the local LIMS system.

Hopefully this solves a problem faced by many labs and prevents too much duplication of work!
Created 02/06/2017 by Aled Jones
'''
#from HTMLParser import HTMLParser
import requests
from bs4 import BeautifulSoup
import pdfkit
import pyodbc
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import sys
import getopt
# Import local settings
from authentication import APIAuthentication # import the function from the authentication script which generates the access token
from gel_report_config import * # config file 
from database_connection_config import * # database connection details


class connect():
	def __init__(self):
		# call function to retrieve the api token
		self.token=APIAuthentication().get_token()
	
		# The link to the first page of the CIP API results
		self.interpretationlist="https://cipapi.genomicsengland.nhs.uk/api/interpretationRequestsList/?format=json&page_size=100000"
		
		# The probandID to return the report for
		self.proband_id=""
		
		# Empty variables for report paths to be generated
		self.html_report=""
		self.pdf_report=""
		
		# A count of GeL records parsed
		self.count=0
		
		# Usage example
		self.usage = "python gel_report.py -g <GELParticipantID>"
		
		# Header line to remove
		self.old_header="Genomics England, Queen Mary University of London,"

		# Old banner colour
		self.existing_banner_css="#007C83; /*#27b7cc;*/"
		
		# new banner colour
		self.new_banner_css=new_banner_colour+";\n    height: 100px;"
				
		# Where to add in new participant information table
		self.where_to_put_new_table="<h3>Participant Information</h3>"
	
	def take_inputs(self, argv):	
		'''Capture the gel participant ID from the command line'''
		# define expected inputs
		try:
			opts, args = getopt.getopt(argv, "g:")
		# raise errors with usage eg
		except getopt.GetoptError:
			print "ERROR - correct usage is", self.usage
			sys.exit(2)
		
		# loop through the arguments 
		for opt, arg in opts:
			if opt in ("-g"):
				# capture the proband ID
				self.proband_id = str(arg)
				
		if self.proband_id:
			#build paths to reports
			self.html_report=html_reports+self.proband_id+".html"
			self.pdf_report=pdf_dir+self.proband_id+".pdf"
			
			# Call the function to read the API
			self.read_API_page()
	
	def read_API_page(self):
		'''This function returns all the cases that can be viewed by the user defined by the authentication token'''
		# use requests module to return all the cases available to you
		# if proxy is set in the config file
		if proxy:
			response = requests.get(self.interpretationlist, headers={"Authorization": "JWT " + self.token},proxies=proxy) # note space is required after JWT 
		else:
			response = requests.get(self.interpretationlist, headers={"Authorization": "JWT " + self.token}) # note space is required after JWT 
		# pass this in the json format to the parse_json function
		self.parse_json(response.json())
		
			
	def parse_json(self,json):
		'''This function takes the json file containing all cases. This is parsed to look for the desired proband id'''
		# Flag to stop the search
		found=False
		
		# loop through the results
		for sample in json['results']:
			# increase the count of patients searched
			self.count += 1
			# look for the desired proband id
			if sample["proband"]==self.proband_id:
				# if sample is blocked ignore
				if sample["last_status"]=="blocked":
					print "last status = blocked for proband "+str(self.proband_id)
					# probably want to raise an exception here
					raise Exception("last status = blocked for proband "+str(self.proband_id))
				else:
					# set flag to stop the search
					found=True
										
					# create a variable to hold the various cip versions
					max_cip_ver=0

					# loop through each report to find the highest cip_version
					for j in range(len(sample["interpreted_genomes"])):
						if int(sample["interpreted_genomes"][j]["cip_version"])>max_cip_ver:
							max_cip_ver=sample["interpreted_genomes"][j]["cip_version"]

					# for the highest cip version
					for j in range(len(sample["interpreted_genomes"])):
						if sample["interpreted_genomes"][j]["cip_version"]==max_cip_ver:
							
							# take the most recent report generated for this CIP API (take the last report from the list of reports)
							print sample["interpreted_genomes"][j]["clinical_reports"][-1]['url']
							# if proxy is set in the config file
							if proxy:
								report=requests.get(sample["interpreted_genomes"][j]["clinical_reports"][-1]['url'],headers={"Authorization": "JWT " + self.token},proxies=proxy)# note space is required after JWT 
							else:
								report=requests.get(sample["interpreted_genomes"][j]["clinical_reports"][-1]['url'],headers={"Authorization": "JWT " + self.token})# note space is required after JWT 

							# create an beautiful soup object for the html clinical report
							soup=BeautifulSoup(report.content,"html.parser")

							#pass the object to the replace_gel_address function and update the object
							soup=self.replace_gel_address(soup)

							#pass to function to modify the header
							soup=self.replace_GeL_logo(soup)

							# pass to function to expand coverage
							soup=self.expand_coverage(soup)
							#print soup
							
							#write html to file
							with open(self.html_report, "w") as file:
								file.write(str(soup))
							
							# Can't change CSS using beautiful soup so need to read and replace html file
							# read file into object (a list)
							with open(self.html_report, "r") as file:
								data=file.readlines()
							#loop through the file object
							for i, line in enumerate(data):
								# if line contains the existing banner css
								if self.existing_banner_css in line:
									#replace that line in the file object
									data[i]=line.replace(self.existing_banner_css,self.new_banner_css)
								
								if self.where_to_put_new_table in line:
									# open template
									with open(new_table,"r") as template:
										template_to_write=template.readlines()
										#print template_to_write
									for template_line in reversed(template_to_write):
										data[i]="".join(template_to_write)
																		
							#write the modified list back to a file
							with open(self.html_report, "w") as file:
								file.writelines(data)
							
							# Call function to pull out patient demographics from LIMS
							self.read_lims()
			
		# if proband not found 
		if not found:
			# print statement to say not found
			print "Record not found in the "+str(self.count) + " GeL records parsed"
			# assert that the number of GEL record parsed == the sample count provided in the JSON
			assert self.count == json['count'], "self.count != gel's count"

	def read_lims(self):
		'''This function must create a dictionary which is used to populate the html variables 
		eg patient_info_dict={"NHS":NHS,"PRU":PRU,"dob":DOB,"firstname":FName,"lastname":LName,"gender":Gender}'''
		# get all of SelectRegister_GMCParticipants_RegisterEntryDetails 
		stored_proc_1="EXECUTE [GeneWorks].[dbo].[SelectRegister_GMCParticipants_RegisterEntryDetails]"
		all_GMC_patients=self.fetchall(stored_proc_1)
		
		# filter using gelparticipantID
		for record in all_GMC_patients:
			if record[7]==self.proband_id:
				PRU=record[2]
				DOB=record[6]
				FName=record[5]
				LName=record[4]
		
		#convert DOB to required format
		DOB=DOB.strftime('%d/%m/%Y')

		# use the PRU to access spSelectPatientDetail to get NHS number
		stored_proc_2="EXECUTE [GeneWorks].[dbo].[spSelectPatientDetail] @PatientID = \""+PRU+"\""
		#print stored_proc_2
		patient_info=self.fetchone(stored_proc_2)
		
		#print len(patient_info)
		
		NHS=patient_info[12]
		Gender=patient_info[4]
		
		if Gender=="M":
			Gender="Male"
		elif Gender=="F":
			Gender="Female"
		else:
			raise Error("The Gender in Geneworks is not 'M' or 'F'")
		
		patient_info_dict={"NHS":NHS,"PRU":PRU,"dob":DOB,"firstname":FName,"lastname":LName,"gender":Gender}
		
		#pass modified file to create a pdf.
		self.create_pdf(self.pdf_report,patient_info_dict)								
		
	
	def replace_gel_address(self,html):
		'''This function loops through the report html object and replaces the GeL address with a rider to say this is an internal report based on the information from the GeL API'''
		# notes is a list of all the p tags where the class == note
		notes=html.find_all("p", class_="note")
		# loop through each p tag and look for the containing the gel address (as defined in the init function)
                for note in range(len(notes)):
			# if the string is in the text
			if self.old_header in notes[note].get_text():
				# create a new <p> tag
				new_rpt_header=html.new_tag("p")
				# add in the new header to the tag string
				new_rpt_header.string=new_header_line
				# create a new break tag
				br=html.new_tag('br')
				# add the break tag to the end of the text string twice
				new_rpt_header.insert(len(new_rpt_header),br)
				new_rpt_header.insert(len(new_rpt_header),br)
				# insert the new tag into the html
				notes[note].insert_before(new_rpt_header)
				# remove the gel address tag
				notes[note].extract()
				# return modified html
				return html

	def replace_GeL_logo(self,html):
		'''This function removes the gel logo and changes the css for the report banner'''
		# find the gel logo and remove it
		for img in html.find_all('img', class_="logo"):
			img['src']=new_logo
		# resize the banner so it doesn't shrink after the logo has been removed
		#for banner in html.find_all('div', class_="banner-text"):
	#		del(banner['class'])
		return html


	def expand_coverage(self,html):
		'''Expand the coverage section'''
		# find the coverage div and delete so coverage seciton no longer needs to be clicked to be visible
		for section in html.find_all('div', id="coverage"):
			del(section['hidden'])

		# find the section header and remove text/hyperlink properties
		for section in html.find_all('a'):
			# find the coverage section
			if "Coverage Metrics" in section.get_text():
				# remove the extra styles no longer needed
				del(section['onclick'])
				del(section['style'])
				# create new tag and section title
				new_header="Coverage Report"
				# replace p with h3
				section.name="h3"
				# change the string
				section.string=new_header
		return html


	def create_pdf(self,pdfreport_path,patient_info):
		# add the path to wkhtmltopdf to the pdfkit config settings
		pdfkitconfig = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
		# create options to use in the footer
		options={'footer-right':'Page [page] of [toPage]','footer-left':'Date Created [isodate]'}
		# use Jinja to populate the variables within the html template
		# first tell the system where to find the html template (this is written by beautiful soup above)
		env = Environment(loader=FileSystemLoader('/home/mokaguys/Documents/GeL_reports/html/'))
		template = env.get_template(self.proband_id+".html")
		# create the pdf using template.render to populate variables from dictionary created in read_geneworks
		pdfkit.from_string(template.render(patient_info), pdfreport_path, options=options, configuration=pdfkitconfig)
		
	def fetchone(self, query):
		# Connection
		cnxn = pyodbc.connect(dbconnectstring)
		# Opening a cursor
		cursor = cnxn.cursor()
		#perform query
		cursor.execute(query)
		#capture result
		result = cursor.fetchone()
		#yield result
		if result:
			return result
			#for i in result:
			#	print i
				#yield(result)
		else:
			print "no result found"
	
	def fetchall(self, query):
		# Connection
		cnxn = pyodbc.connect(dbconnectstring)
		# Opening a cursor
		cursor = cnxn.cursor()
		#perform query
		cursor.execute(query)
		#capture result
		result = cursor.fetchall()
		#yield result
		if result:
			return(result)
		else:
			print "no result found"
		
if __name__=="__main__":
	c=connect()
	c.take_inputs(sys.argv[1:])
