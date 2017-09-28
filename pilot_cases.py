'''
gel_report.py
This script takes a GEL Participant ID and queries the CIP-API to return a clinical report.

This report is then modified to make it clear that this report has not been issued by GEL, including extracting some information from the local LIMS system.

Hopefully this solves a problem faced by many labs and prevents too much duplication of work!
Created 02/06/2017 by Aled Jones
'''
import requests
from bs4 import BeautifulSoup
import pdfkit
import pyodbc
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import sys
import getopt
import json

# Import local settings
from authentication import APIAuthentication # import the function from the authentication script which generates the access token
from gel_report_config import * # config file 
from database_connection_config import * # database connection details


class connect():
	def __init__(self):
		# call function to retrieve the api token
		self.token=APIAuthentication().get_token()
	
		# The link to the first page of the CIP API results
		self.interpretationlist="https://cipapi.genomicsengland.nhs.uk/api/interpretationRequestsList/?format=json"
		
		# The link for the interpretationRequest
		self.interpretationrequest="https://cipapi.genomicsengland.nhs.uk/api/interpretationRequests/%s/%s/?format=json"
		
		# The probandID to return the report for
		self.proband_id=""
		
		# A count of GeL records parsed
		self.pilot_count=0
		
		self.totaln=0
		
		#list of blocked samples
		self.blocked = []
		
		# list of neg_neg
		self.negneg=[]
		
		# self.neg_pos
		self.negpos=[]
		
		#list for pilot
		self.unblocked_pilot_case=[]
		
		#list for main programme
		self.non_pilot_case=[]
		
		# count from API
		self.api_count=0
		
		# create a variable to hold the various cip versions
		self.max_cip_ver=0
	
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
		#print "have read the API"
		# pass this in the json format to the parse_json function
		return response.json()
		
			
	def parse_json(self,json):
		'''This function takes the json file containing all cases. This is parsed to look for the desired proband id'''
		self.api_count=json['count']
		
		# loop through the results
		for sample in json['results']:
			# capture proband id
			self.proband=sample["proband"]
			
			#count total samples assessed
			self.totaln += 1
			
			#if pilot case
			if int(self.proband) > 49999999 and int(self.proband) < 59999999:
				# increase the count of patients searched
				self.pilot_count += 1
				
				# if sample is blocked record and skip
				if sample["last_status"]=="blocked":
					self.blocked.append(self.proband)
				
				else:
					self.unblocked_pilot_case.append(self.proband)
					
					# retrieve the interpretation report id
					ir_id  = sample['interpretation_request_id'].split('-')[0]
					version = sample['interpretation_request_id'].split('-')[1]
					
					# build the url
					self.read_interpretation_request(self.interpretationrequest % (ir_id,version))
					
					#change url back for next sample
					self.interpretationlist = self.interpretationlist
			
			# if it's not a pilot case record and stop
			else:
				self.non_pilot_case.append(self.proband)
			
		# at end of the list read the next page
		if json['next']:
			# Call the function to read the API with url for next page
			json=self.read_API_page(json['next'])
			#send result to parse_json function
			self.parse_json(json)
		else:
			# check the count is same as expected number of cases as per API
			assert self.totaln == self.api_count
			#check the number of pilot and non pilot == totaln
			assert len(self.non_pilot_case) + self.pilot_count == self.totaln
			#check all pilot cases are accounted for
			assert len(self.unblocked_pilot_case) + len(self.blocked) == self.pilot_count
			#check number of negative negative cases plus non-negative negative cases add up to unblocked cases
			assert len(self.negneg)+len(self.negpos)==len(self.unblocked_pilot_case)
			
			# print statements to say not found
			print "samples in api = "+ str(self.api_count)
			print "samples read from api = "+ str(self.totaln)
			print "number of non pilot = " + str(len(self.non_pilot_case))
			print "number of pilot = " + str(self.pilot_count)
			print "number of blocked pilot cases= " + str(len(self.blocked))
			print "number of unblocked pilot cases= " + str(len(self.unblocked_pilot_case))
			print "number of negative negative cases = " + str(len(self.negneg))
			#print self.negneg
			print "number of cases with variants = " + str(len(self.negpos))
			
	def read_interpretation_request(self,url):
		# pass the url to the function which reads the url. assign to interpretation_request
		interpretation_request=self.read_API_page(url)
		
		# loop through each report to find the highest cip_version
		for j in range(len(interpretation_request["interpreted_genome"])):
			if int(interpretation_request["interpreted_genome"][j]["cip_version"])>self.max_cip_ver:
				self.max_cip_ver=interpretation_request["interpreted_genome"][j]["cip_version"]
		
		#set flag to mark this case as positive or negative
		positive=False
		
		# loop through the interpreted_genome, looking for the one with highest cip version
		for interpreted_genome in interpretation_request['interpreted_genome']:
			# if it's the highest cip version
			if interpreted_genome['cip_version'] == self.max_cip_ver:
				# see if there are any tiered variants (these are in a list)
				for variant in interpretation_request['interpretation_request_data']['json_request']['TieredVariants']:
						# there can be a list of classifications for a variant eg if the gene is in multiple panels. loop through these incase one panel has a different tier to the others
						for i in range(len(variant['reportEvents'])):
							# Look for tier1 and tier2 variants (ignore tier3)
							if variant['reportEvents'][i]['tier'] in ["TIER1","TIER2"]:
								# if present mark case as positive 
								positive=True
				#next look at CIP candidate variants, but no need to look if case already has tier1 or tier2 variant
				if positive:
					pass
				else:
					# loop through each variant in interpreted genome section
					for variant in range(len(interpreted_genome['interpreted_genome_data']['reportedVariants'])):
						# loop through each reportevent (one variant can have different tiers)
						for report_event in range(len(interpreted_genome['interpreted_genome_data']['reportedVariants'][variant]['reportEvents'])):
									# if there is a tier 1 or tier 2, mark case as positive
									if interpreted_genome['interpreted_genome_data']['reportedVariants'][variant]['reportEvents'][report_event]['tier'] in ["TIER1","TIER2"]:
										positive=True
		#if a tier1 or 2 variant has been seen add probandid to the dict
		if positive:
			self.negpos.append(self.proband)
		#otherwise add to the negative dict
		else:
			self.negneg.append(self.proband)
					
if __name__=="__main__":
	c=connect()
	c.build_url()
