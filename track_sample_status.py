'''
This script reads the CIP-API, identifies any probands which have been sent to the GMC for review (using the status field) and will enable these to be imported into moka.
'''
import requests
import pyodbc
import json
import datetime

# Import local settings
from authentication import APIAuthentication # import the function from the authentication script which generates the access token
from database_connection_config import * # database connection details
from gel_report_config import * # config file 


class connect():
	def __init__(self):
		# call function to retrieve the api token
		self.token=APIAuthentication().get_token()
	
		# The link to the first page of the CIP API results
		self.interpretationlist="https://cipapi.genomicsengland.nhs.uk/api/interpretationRequestsList/?format=json"
		
		# list to hold probands in moka
		self.moka=[]
		
		# moka statuses used to track samples
		self.awaiting_analysis_status="1202218824" # default status when first added to db
		self.main="1202218828" # status to denote main program
		self.pilot="1202218827" # status to denote main program
		
		# variables for the database connection
		#self.cnxn = pyodbc.connect(mokadevdb)
		#self.cursor = self.cnxn.cursor()
		
		# variables to hold queries
		self.select_qry = ""
		self.insert_query = ""
		
		# dict to hold probands and IRs
		self.omicia_pilot={}
		self.omicia_main={}
		self.now=datetime.datetime.now()
		self.now=self.now.strftime('%Y-%m-%d %H:%M:%S')
				
		
	def build_url(self):	
		'''Capture the gel participant ID from the command line'''		
		#print "about to read API"
		# Call the function to read the API
		json=self.read_API_page(self.interpretationlist)
		self.parse_json(json)
	
	def read_API_page(self, url):
		'''This function returns all the cases that can be viewed by the user defined by the authentication token'''
		# use requests module to return all the cases available to you
		# if proxy is set in the config file
		if proxy:
			response = requests.get(url, headers={"Authorization": "JWT " + self.token},proxies=proxy) # note space is required after JWT 
		else:
			response = requests.get(url, headers={"Authorization": "JWT " + self.token}) # note space is required after JWT 
		
		# pass this in the json format to the parse_json function
		return response.json()
	
	
	def parse_json(self,json):
		'''This function takes the json file containing all interpretation requests. 
		Idea is that the script is run regularly, before any analysis occurs, looking for the status of sent_to_gmc. 
		If the proband is not already in moka insert it'''
		# loop through the results
		for sample in json['results']:			
			proband=sample['proband']
			#if pilot case
			if "GSTT" in sample['sites']:			
				# only samples where status == sent_to_gmcs
				if sample["last_status"] in ["sent_to_gmcs","report_generated","report_sent"]:
					# check we are only looking at omicia interpretation requests
					if sample["cip"]==CIP:
						# check if proband is in dictionary
						if proband in self.omicia_pilot:
							# if it is add the IR ID
							self.omicia_pilot(proband).append(sample['interpretation_request_id'])
						else:
							# else add to dict
							self.omicia_pilot[proband]=[sample['interpretation_request_id']]
					# if not Omicia CIP
					else:
						pass
						
			# if it's main program...
			else:
				# only samples where status == sent_to_gmcs
				if sample["last_status"] in ["sent_to_gmcs","report_generated","report_sent"]:
					# #check we are only looking at omicia interpretation requests
					if sample["cip"]==CIP:
						# check if proband is in dictionary
						if proband in self.omicia_main:
							# if it is add the IR ID
							self.omicia_main(proband).append(sample['interpretation_request_id'])
						else:
							# else add to dict
							self.omicia_main[proband]=[sample['interpretation_request_id']]
					# if not Omicia CIP
					else:
						pass
				
			
		# at end of the list read the next page
		if json['next']:
			# Call the function to read the API with url for next page
			json=self.read_API_page(json['next'])
			#send result to parse_json function
			self.parse_json(json)
		else:
			# read moka
			#self.pull_out_moka()
			
			# whilst moka cannot be read from server create manually
			self.moka=[]
			
			# call function to insert/summarise
			self.insert_to_moka()
		
	def insert_to_moka(self):
		'''This function loops through the dictionary populated above and captures the highest interpretation request.
		It checks that there aren't two different unblocked interpretation requests (for the same cip)'''
		#loop through probands in dict
		for proband in self.omicia_pilot:
			#set empty values for Interpretation requests 
			IR_id=0
			version=0
			# if multiple interpretation requests
			if len(self.omicia_pilot[proband])>1:
				for IR in self.omicia_pilot[proband]:					
					# first time capture the IR_ID
					if IR_id==0:
						IR_id==IR.split('-')[0]
					# The IR_ID should be the same for each proband.
					elif IR_id!=IR.split('-')[0]:
						print 'Different Interpretation request IDs for same proband ('+str(proband)+', same CIP'
					
					# capture the highest version
					if IR.split('-')[1] > version:
						version=IR.split('-')[1]
			else:
				for IR in self.omicia_pilot[proband]:	
					IR_id=int(IR.split('-')[0])
					version=int(IR.split('-')[1])
			
			# build the insert to moka queries
			#if already in moka pass
			if proband in self.moka:
				pass
			else:
				# else built insert query
				self.insert_query = "insert into dbo.[GEL100KAnalysisStatus] (GEL_ProbandID,IR_ID,GEL_programme,Lab_Status,DateAdded) values (%s,'%s',%s,%s,'%s')"%(proband,str(IR_id)+"-"+str(version),self.pilot,self.awaiting_analysis_status,self.now)
				# until database is connected to moka just print the query
				print self.insert_query
				
				# execute the sql insert
				# self.insert_query_function()
		
		# repeat for main program cases
		for proband in self.omicia_main:
			#set empty values for Interpretation requests 
			IR_id=0
			version=0
			# if multiple interpretation requests
			#print self.omicia_main[proband]
			if len(self.omicia_main[proband])>1:
				for IR in self.omicia_main[proband]:
					# first time capture the IR_ID				
					if IR_id==0:
						IR_id==int(IR.split('-')[0])
					# The IR_ID should be the same for each proband.
					elif IR_id!=IR.split('-')[0]:
						print 'Different Interpretation request IDs for same proband ('+str(proband)+', same CIP'
					
					# capture the highest version
					if IR.split('-')[1] > version:
						version=IR.split('-')[1]
			else:
				for IR in self.omicia_main[proband]:
					IR_id=int(IR.split('-')[0])
					version=int(IR.split('-')[1])
					
			# build the insert to moka queries
			#if already in moka pass
			if proband in self.moka:
				pass
			else:
				# else built insert query
				self.insert_query = "insert into dbo.[GEL100KAnalysisStatus] (GEL_ProbandID,IR_ID,GEL_programme,Lab_Status,DateAdded) values (%s,'%s',%s,%s,'%s')"%(proband,str(IR_id)+"-"+str(version),self.main,self.awaiting_analysis_status,self.now)
				#self.insert_query_function()
				print self.insert_query
		
	def pull_out_moka(self):
		''' read all probands already in moka'''	
		#get all gel_probands in moka
		self.select_qry="select GEL_ProbandID from dbo.[100KAnalysisStatus]"
		self.moka = self.select_query()
		
	def insert_query_function(self):
		'''This function executes an insert query'''
		# execute the insert query
		self.cursor.execute(self.insert_query)
		self.cursor.commit()
		
	def select_query(self):
		'''This function is called to retrieve the whole result of a select query '''
		# Perform query and fetch all
		result = self.cursor.execute(self.select_qry).fetchall()

		# return result
		if result:
		    return(result)
		else:
			result=[]
			return(result)#raise Exception(self.select_qry_exception)
			
					
if __name__=="__main__":
	c=connect()
	c.build_url()
