'''
pilot_cases.py
This script reads the CIP-API and summarises the state of play for (mostly) pilot cases.
It reports how many cases are ready for analysis, how many are negative negatives etc.
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
		
		# A list of GeL records parsed
		self.pilot_count=[]
		
		self.totaln=0
		
		#list of blocked samples
		self.pilot_blocked = []
		#not ready to analyse
		self.not_ready_for_analysis=[]
		# list of neg_neg
		self.negneg_pilot=[]
		
		# self.neg_pos
		self.negpos_pilot=[]
		
		# list of omicia's
		self.omicia_pilot=[]
		self.omicia_probands_pilot=[]
		self.non_omicia_pilot=[]
		
		#list of cases can't determine status
		self.undetermined_pilot=[]
		
		#list for pilot
		self.pilot_unblocked=[]
		
		#list for main programme
		self.non_pilot_case=[]
		
		# count from API
		self.api_count=0
		
		# create a variable to hold the various cip versions
		self.max_cip_ver=0
		
		# all pilot probands from clinic
		self.pilot_proband_list_from_clinic=[50002725,50003467,50003437,50003384,50004265,50004170,50004371,50001343,50001503,50001470,50004147,50004009,50004241,50003506,50004169,50002319,50002476,50002524,50002418,50001332,50001493,50001459,50002253,50003766,50004234,50003806,50003468,50003398,50003763,50003955,50003862,50003621,50003582,50003665,50002250,50003796,50004174,50002444,50002330,50002493,50004235,50004232,50002772,50002277,50002842,50002442,50002730,50003807,50003797,50003798,50003857,50003952,50003759,50003809,50003800,50003801,50003802,50003810,50002721,50002727,50002728,50002729,50002769,50004374,50003313,50003317,50003639,50003609,50003319,50003320,50003439,50003390,50004387,50003514,50004363,50004372,50003516,50003804,50003805,50003881,50003761,50003859,50004288,50004410,50003767,50003864,50003956,50002417,50002275,50002422,50002477,50002523,50002318,50003637,50002666,50002559,50002699,50002560,50002667,50004690,50003957,50003768,50004074,50003861,50003958,50003865,50003776,50003959,50003799,50003808,50004010,50004099,50004066,50004148,50004021,50004152,50004104,50004156,50004024,50004107,50004025,50004154,50004155,50004106,50004026,50004175,50004268,50004379,50004440,50004289,50004411,50004204,50004233,50004238,50004666,50004239,50004450,50004582,50004683,50004698,50004808,50001829,50001914,50001945,50001871,50002136,50002023,50002095,50004182,50004385,50004661,50004795,50004719,50004176,50002252,50003510,50003459,50003434,50003311,50003586,50003655,50003432,50004448,50004205,50004060,50004287,50002771,50002894,50002774,50002482,50002323,50002425,50002513,50002093,50002024,50002134,50002514,50003053,50002958,50003196,50003498,50002726,50003636,50002427,50003947,50003853,50003753,50003515,50002416,50002475,50002317,50004240,50003318,50003389,50003465,50003438,50003871,50003773,50003969,50003968,50002691,50002552,50003682,50003677,50003489,50003667,50003409,50003587,50003433,50004102,50004016,50004058,50003507]
		
		# a list of gel proband ids from the apreadsheet containing all the referring clinician info
		#self.spreadsheet_with_referring_clinician_info=[50002725,50003467,50003437,50003384,50004265,50004170,50004371,50001343,50001503,50001470,50004147,50004009,50004241,50003506,50004169,50002319,50002476,50002524,50002418,50001332,50001493,50001459,50002253,50003766,50004234,50003806,50003468,50003398,50003763,50003955,50003862,50003621,50003582,50003665,50002250,50003796,50004174,50002444,50002330,50002493,50004235,50004232,50002772,50002277,50002842,50002442,50002730,50003807,50003797,50003798,50003857,50003952,50003759,50003809,50003800,50003801,50003802,50003810,50002721,50002727,50002728,50002729,50002769,50004374,50003313,50003317,50003639,50003609,50003319,50003320,50003439,50003390,50004387,50003514,50004363,50004372,50003516,50003804,50003805,50003881,50003761,50003859,50004288,50004410,50003767,50003864,50003956,50002417,50002275,50002422,50002477,50002523,50002318,50003637,50002666,50002559,50002699,50002560,50002667,50004690,50003957,50003768,50004074,50003861,50003958,50003865,50003776,50003959,50003799,50003808,50004010,50004099,50004066,50004148,50004021,50004152,50004104,50004156,50004024,50004107,50004025,50004154,50004155,50004106,50004026,50004175,50004268,50004379,50004440,50004289,50004411,50004204,50004233,50004238,50004666,50004239,50004450,50004582,50004683,50004698,50004808,50001829,50001914,50001945,50001871,50002136,50002023,50002095,50004182,50004385,50004661,50004795,50004719,50004176,50002252,50003510,50003459,50003434,50003311,50003586,50003655,50003432,50004448,50004205,50004060,50004287,50002771,50002894,50002774,50002482,50002323,50002425,50002513,50002093,50002024,50002134,50002514,50003053,50002958,50003196,50003498,50002726,50003636,50002427,50003947,50003853,50003753,50003515,50002416,50002475,50002317,50004240,50003318,50003389,50003465,50003438,50003871,50003773,50003969,50003968,50002691,50002552,50003682,50003677,50003489,50003667,50003409,50003587,50003433,50004102,50004016,50004058,50003507]
		
		# a list of gel proband ids from the spreadsheet containing all the referring clinician info after chase up 
		self.spreadsheet_with_referring_clinician_info=[50002412,50002252,50003311,50002413,50002414,50002415,50003947,50003853,50003753,50002769,50004374,50002558,50002416,50002475,50002317,50004710,50002982,50004683,50003754,50002767,50004017,50004450,50004582,50002417,50002275,50004023,50003580,50002725,50002691,50002552,50004016,50002411,50004661,50004795,50002018,50003498,50002726,50004010,50004099,50004066,50004148,50003467,50003437,50003384,50003516,50003804,50003805,50003881,50004265,50004170,50004371,50002017,50001343,50001503,50001470,50004147,50004009,50003762,50002419,50002513,50002093,50002024,50002134,50002514,50004183,50004241,50003579,50002420,50002970,50003581,50002251,50003506,50003511,50004169,50002731,50003053,50002958,50003196,50002946,50002019,50003381,50004027,50002553,50002421,50004156,50004024,50004107,50002319,50002476,50002524,50002418,50003554,50002994,50004719,50001332,50001493,50001459,50004289,50004411,50004204,50004732,50002253,50002721,50003514,50004363,50004372,50002554,50002770,50001871,50003510,50003459,50003434,50002422,50002477,50002523,50002318,50003316,50001828,50002555,50002768,50003761,50003859,50004288,50004410,50002365,50004171,50004448,50004205,50004060,50004287,50003803,50002935,50002045,50002423,50003387,50002136,50002023,50002095,50003755,50003320,50004025,50004154,50003586,50003655,50003432,50003509,50002482,50002323,50002425,50003388,50004175,50004268,50004379,50004440,50003637,50002666,50002559,50003508,50001377,50003383,50002046,50004698,50004808,50003505,50003439,50003390,50004387,50003553,50003210,50002021,50003315,50004176,50003636,50002427,50002254,50004155,50004106,50004026,50003397,50003391,50002044,50003587,50003005,50003771,50003396,50001333,50002014,50002727,50003772,50004237,50003314,50003127,50004238,50004666,50001582,50002047,50003515,50003507,50004182,50004385,50002366,50001829,50001914,50001945,50002728,50002048,50004177,50003871,50003773,50003969,50003968,50003017,50004233,50003382,50003018,50002022,50003321,50003006,50004671,50004020,50003774,50003775,50002040,50002947,50003861,50003958,50003865,50003776,50003959,50004690,50003957,50003768,50004074,50002043,50003313,50002699,50002560,50002667,50004239,50004236,50003385,50004184,50003318,50002561,50003317,50003639,50003609,50002042,50003319,50002729,50002774,50003399,50003386,50003767,50003864,50003956,50002364,50002562,50003389,50003465,50003438,50003588,50004173,50003766,50004234,50003806,50003468,50003398,50004203,50004021,50004152,50004104,50003763,50003955,50003862,50003621,50003582,50003665,50002041,50004058,50002250,50003765,50004022,50002445,50003796,50003764,50004174,50003769,50003756,50002444,50002330,50002493,50002443,50002249,50004235,50004232,50003770,50004206,50002772,50002277,50002842,50002442,50004012,50004172,50004019,50002020,50002730,50003807,50002441,50002771,50002894,50003757,50002440,50004701,50004018,50002773,50004185,50003798,50003799,50003583,50003758,50003857,50003952,50003759,50003760,50004011,50003808,50003797,50003809,50004207,50004240,50003800,50003801,50003802,50003810,50004102,50003682,50003677,50003489,50003667,50003409,50003433]
		
		# a list of gel proband ids marked as probands from the spreadsheet containing all the pilot cases (from GeL)
		self.list_of_probands_in_spreadsheet=[50002412,50002252,50003311,50002413,50002414,50002415,50004016,50003753,50002769,50002558,50002416,50004710,50002982,50004683,50003754,50002767,50004017,50002417,50004023,50003580,50002725,50002552,50002411,50004661,50002018,50002726,50004010,50003384,50003516,50004170,50002017,50001343,50004009,50003762,50002419,50002024,50004183,50004241,50003579,50002420,50002970,50003581,50002251,50003506,50003511,50004169,50002731,50002958,50002946,50002019,50003381,50004027,50002553,50002421,50004024,50002418,50003554,50002994,50004719,50001332,50004204,50004732,50002253,50002721,50003514,50002554,50002770,50001871,50003510,50002422,50003316,50001828,50002555,50002768,50003761,50002365,50004171,50004205,50003803,50002935,50002045,50002423,50003387,50002023,50003755,50003320,50004025,50003586,50003509,50002425,50003388,50004175,50002559,50003508,50001377,50003383,50002046,50004698,50003505,50003390,50003553,50003210,50002021,50003315,50004176,50002427,50002254,50004026,50003397,50003391,50002044,50003587,50003005,50003771,50003396,50001333,50002014,50002727,50003772,50004237,50003314,50003127,50004238,50001582,50002047,50003515,50003507,50004182,50002366,50001829,50002728,50002048,50004177,50003773,50003017,50004233,50003382,50003018,50002022,50003321,50003006,50004671,50004020,50003774,50002040,50002947,50003776,50003768,50002043,50003313,50002560,50004239,50004236,50003385,50004184,50003318,50002561,50003317,50002042,50003319,50002729,50002774,50003399,50003386,50003767,50002364,50002562,50003389,50003588,50004173,50003766,50004234,50003398,50004203,50004021,50003763,50003582,50002041,50004058,50002250,50003765,50004022,50002445,50003796,50003764,50004174,50003769,50003756,50002444,50002443,50002249,50004235,50004232,50003770,50004206,50002772,50002442,50004012,50004172,50004019,50002020,50002730,50003807,50002441,50002771,50003757,50002440,50004018,50002773,50004185,50003797,50003798,50003799,50003583,50003758,50003759,50003760,50004011,50003808,50003809,50004207,50004240,50003800,50003801,50003802,50003810,50004701,50004450,50003775]
			
		# a list of all gel proband ids from the spreadsheet containing all the pilot cases (from GeL)
		self.all_gel_ids_in_spreadsheet=[50001332,50001333,50001343,50001377,50001459,50001470,50001493,50001495,50001503,50001504,50001582,50001618,50001630,50001642,50001737,50001749,50001761,50001773,50001828,50001829,50001871,50001914,50001944,50001945,50002007,50002014,50002017,50002018,50002019,50002020,50002021,50002022,50002023,50002024,50002040,50002041,50002042,50002043,50002044,50002045,50002046,50002047,50002048,50002080,50002089,50002092,50002093,50002094,50002095,50002107,50002108,50002109,50002110,50002111,50002112,50002130,50002133,50002134,50002135,50002136,50002137,50002149,50002150,50002151,50002152,50002153,50002154,50002155,50002168,50002169,50002170,50002172,50002173,50002174,50002178,50002179,50002249,50002250,50002251,50002252,50002253,50002254,50002275,50002277,50002315,50002316,50002317,50002318,50002319,50002320,50002321,50002323,50002328,50002330,50002364,50002365,50002366,50002411,50002412,50002413,50002414,50002415,50002416,50002417,50002418,50002419,50002420,50002421,50002422,50002423,50002425,50002427,50002440,50002441,50002442,50002443,50002444,50002445,50002473,50002474,50002475,50002476,50002477,50002478,50002479,50002480,50002482,50002491,50002492,50002493,50002494,50002508,50002513,50002514,50002515,50002516,50002517,50002518,50002522,50002523,50002524,50002525,50002526,50002527,50002535,50002546,50002547,50002548,50002549,50002552,50002553,50002554,50002555,50002558,50002559,50002560,50002561,50002562,50002649,50002656,50002657,50002658,50002659,50002660,50002666,50002667,50002668,50002674,50002690,50002691,50002692,50002693,50002698,50002699,50002712,50002721,50002725,50002726,50002727,50002728,50002729,50002730,50002731,50002732,50002733,50002748,50002767,50002768,50002769,50002770,50002771,50002772,50002773,50002774,50002830,50002831,50002832,50002835,50002842,50002894,50002920,50002921,50002935,50002946,50002947,50002958,50002970,50002982,50002994,50003005,50003006,50003017,50003018,50003039,50003053,50003073,50003075,50003079,50003082,50003085,50003090,50003097,50003101,50003107,50003123,50003126,50003127,50003149,50003159,50003167,50003169,50003181,50003193,50003196,50003210,50003275,50003286,50003311,50003312,50003313,50003314,50003315,50003316,50003317,50003318,50003319,50003320,50003321,50003381,50003382,50003383,50003384,50003385,50003386,50003387,50003388,50003389,50003390,50003391,50003396,50003397,50003398,50003399,50003407,50003409,50003411,50003414,50003416,50003417,50003418,50003419,50003432,50003433,50003434,50003435,50003436,50003437,50003438,50003439,50003440,50003443,50003459,50003460,50003461,50003462,50003463,50003464,50003465,50003466,50003467,50003468,50003471,50003472,50003478,50003484,50003486,50003489,50003490,50003491,50003492,50003498,50003499,50003500,50003505,50003506,50003507,50003508,50003509,50003510,50003511,50003514,50003515,50003516,50003553,50003554,50003579,50003580,50003581,50003582,50003583,50003586,50003587,50003588,50003590,50003592,50003601,50003605,50003608,50003609,50003612,50003621,50003622,50003624,50003625,50003631,50003633,50003636,50003637,50003638,50003639,50003643,50003646,50003652,50003653,50003655,50003657,50003665,50003666,50003667,50003673,50003677,50003679,50003681,50003682,50003753,50003754,50003755,50003756,50003757,50003758,50003759,50003760,50003761,50003762,50003763,50003764,50003765,50003766,50003767,50003768,50003769,50003770,50003771,50003772,50003773,50003774,50003775,50003776,50003794,50003795,50003796,50003797,50003798,50003799,50003800,50003801,50003802,50003803,50003804,50003805,50003806,50003807,50003808,50003809,50003810,50003853,50003854,50003855,50003856,50003857,50003858,50003859,50003860,50003861,50003862,50003863,50003864,50003865,50003866,50003867,50003868,50003869,50003870,50003871,50003872,50003873,50003881,50003882,50003947,50003948,50003949,50003950,50003951,50003952,50003953,50003954,50003955,50003956,50003957,50003958,50003959,50003960,50003961,50003962,50003963,50003964,50003965,50003966,50003967,50003968,50003969,50003970,50003979,50004009,50004010,50004011,50004012,50004016,50004017,50004018,50004019,50004020,50004021,50004022,50004023,50004024,50004025,50004026,50004027,50004058,50004060,50004064,50004066,50004074,50004075,50004077,50004099,50004100,50004102,50004103,50004104,50004105,50004106,50004107,50004108,50004115,50004119,50004120,50004122,50004147,50004148,50004149,50004151,50004152,50004153,50004154,50004155,50004156,50004157,50004159,50004161,50004162,50004163,50004166,50004169,50004170,50004171,50004172,50004173,50004174,50004175,50004176,50004177,50004182,50004183,50004184,50004185,50004203,50004204,50004205,50004206,50004207,50004232,50004233,50004234,50004235,50004236,50004237,50004238,50004239,50004240,50004241,50004260,50004265,50004266,50004267,50004268,50004273,50004287,50004288,50004289,50004347,50004348,50004349,50004350,50004359,50004360,50004361,50004362,50004363,50004364,50004371,50004372,50004373,50004374,50004375,50004376,50004377,50004378,50004379,50004385,50004386,50004387,50004388,50004389,50004390,50004409,50004410,50004411,50004439,50004440,50004448,50004450,50004451,50004582,50004654,50004661,50004666,50004671,50004681,50004683,50004690,50004698,50004701,50004702,50004704,50004710,50004719,50004732,50004741,50004745,50004750,50004754,50004770,50004795,50004808,50004835,50004850,50004853,50004854]
		
		# a list of gel proband ids marked as non-probands from the spreadsheet containing all the pilot cases (from GeL)
		self.list_of_non_probands_in_spreadsheet=[50001459,50001470,50001493,50001503,50001914,50001945,50002093,50002095,50002134,50002136,50002275,50002277,50002317,50002318,50002319,50002323,50002330,50002475,50002476,50002477,50002482,50002493,50002513,50002514,50002523,50002524,50002666,50002667,50002691,50002699,50002842,50002894,50003053,50003196,50003409,50003432,50003433,50003434,50003437,50003438,50003439,50003459,50003465,50003467,50003468,50003489,50003498,50003609,50003621,50003636,50003637,50003639,50003655,50003665,50003667,50003677,50003682,50003804,50003805,50003806,50003853,50003857,50003859,50003861,50003862,50003864,50003865,50003871,50003881,50003947,50003952,50003955,50003956,50003957,50003958,50003959,50003968,50003969,50004060,50004066,50004074,50004099,50004102,50004104,50004106,50004107,50004147,50004148,50004152,50004154,50004155,50004156,50004265,50004268,50004287,50004288,50004289,50004363,50004371,50004372,50004374,50004379,50004385,50004387,50004410,50004411,50004440,50004448,50004582,50004666,50004690,50004795,50004808]
		
	def build_url(self):	
		'''Capture the gel participant ID from the command line'''		
		#print "about to read API"
		# Call the function to read the API
		json=self.read_API_page(self.interpretationlist)
		self.parse_json(json)
	
	def read_API_page(self, url):
		'''This function returns the page requested from the given url'''
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
			if "GSTT" in sample['sites']:
				# add proband to list of pilot probands
				self.pilot_count.append(sample["proband"])
				
				# if sample is blocked record and skip
				if sample["last_status"]=="blocked":
					self.pilot_blocked.append(self.proband)
				# if status is one which mwans the sample hasn't yet been sent to the lab for analysis record and stop
				elif sample["last_status"] in ("waiting_payload","interpretation_generated","dispatched","files_copied","transfer_ready","transfer_complete","rejected_wrong_format","gel_qc_failed","gel_qc_passed"):
					self.not_ready_for_analysis.append(self.proband)
				# all other cases have been shared with the lab
				else:
					# add the proband to list of unblocked probands
					self.pilot_unblocked.append(self.proband)
					
					# #check we are only looking at omicia interpretation requests
					if sample["cip"]==CIP:
						# add this proband to a list of probands that have been sent to omicia
						self.omicia_probands_pilot.append(sample['proband'])
						# also add a tuple of the interpretation request and proband to a list
						self.omicia_pilot.append((sample['proband'],sample['interpretation_request_id']))
						
						# retrieve the interpretation report id
						ir_id  = sample['interpretation_request_id'].split('-')[0]
						version = sample['interpretation_request_id'].split('-')[1]
						
						# call the function which reads the interpretation request
						self.read_interpretation_request(self.interpretationrequest % (ir_id,version))
					else:
						# otherwise is not an omicia interpretation request so count and stop
						self.non_omicia_pilot.append((sample['proband'],sample['interpretation_request_id']))
			
			# if it's not a pilot case record and stop
			else:
				self.non_pilot_case.append(self.proband)
			
		# at end of the list read the next page
		if json['next']:
			# Call the function to read the API with url for next page
			json=self.read_API_page(json['next'])
			#send result to parse_json function
			self.parse_json(json)
		
		# if no more pages to read have assessed all interpretation requests in the API
		else:
			#perform some checks that the maths add up.
			
			# check the count is same as expected number of cases as per API
			assert self.totaln == self.api_count
			#check the number of pilot and non pilot == totaln
			assert len(self.non_pilot_case) + len(self.pilot_count) == self.totaln
			#check all pilot cases are accounted for
			assert len(self.pilot_unblocked) +len(self.not_ready_for_analysis)+ len(self.pilot_blocked) == len(self.pilot_count)
			#check number of negative negative cases plus non-negative negative cases add up to unblocked cases
			assert len(self.negneg_pilot)+len(self.negpos_pilot)+len(self.undetermined_pilot)==len(self.omicia_pilot)
			#check number of omicia cases + non omicia cases add up to unblocked cases
			assert len(self.non_omicia_pilot)+len(self.omicia_pilot)==len(self.pilot_unblocked)
			
			# Blocked probands may have another interpretation request which is not blocked.
			truely_blocked_pilot=[]
			# for each proband in blocked list
			for blocked_pilot in set(self.pilot_blocked):
				#if its not in omicia list
				if blocked_pilot not in self.omicia_probands_pilot:
					# then it is truely blocked
					truely_blocked_pilot.append(blocked_pilot)
			
			# count how many probands are still being processed and haven't been sent to the GMC yet
			different_status_pilot=[]
			# for each proband which has a different status
			for diff_status in set(self.not_ready_for_analysis):
				# if its not in omicia list (ie if it hasn't already been shared with GMC)
				if diff_status not in self.omicia_probands_pilot:
					# add to list
					different_status_pilot.append(diff_status)
					
			# print summary statements
			print "samples in api = "+ str(self.api_count)
			print "samples read from api = "+ str(self.totaln)
			#print "number of non pilot probands = " + str(len(self.non_pilot_case))
			print "number of unique non-pilot = " + str(len(set(self.non_pilot_case)))
			print "number of unique pilot = " + str(len(set(self.pilot_count)))
			print "number of unique blocked pilot probands = " + str(len(set(truely_blocked_pilot)))
			print "number of unique pilot probands not yet ready for analysis by GMC= " + str(len(set(different_status_pilot)))
			print "number of unique unblocked pilot cases= " + str(len(set(self.omicia_probands_pilot)))
			print "number of pilot negative negative cases = " + str(len(self.negneg_pilot))
			print "number of pilot cases with variants = " + str(len(self.negpos_pilot))
			print "number of cases cannot determine # variants = " + str(len(self.undetermined_pilot))
			print "number of pilot omicia interpretation requests = " + str(len(self.omicia_pilot))
			print "number of pilot non-omicia interpretation requests = " + str(len(self.non_omicia_pilot))
			print "number of pilot probands with > 1 unblocked interpretation requests (from same CIP) = " + str(len(self.omicia_pilot)-len(set(self.pilot_count))+len(set(different_status_pilot)))
			
			#print map(str,self.negneg_pilot)
			
			##################TESTS FOR PILOT CASES NOT STARTING WITH 5, or MAIN PROGRAMME CASES STARTING WITH 5#####################
			# check if all pilot cases start with 5
			for i in self.pilot_unblocked:
				if str(i).startswith("5"):
					pass
				else:
					print "pilot cases not starting with 5" + str(i)
			
			# check if any main prog cases start with 5
			for i in self.non_pilot_case:
				if str(i).startswith("5"):
					print "non pilot case starting with 5:"+str(i)
			
			###############Identify the probands with multiple unblocked interpretation requests##########
			# #empty dict to hold interpretation requests for each proband	
			# multiple_IR={}
			# #loop through list
			# for i in self.omicia_pilot:
				# # get proband from tuple
				# proband = i[0]
				# # add proband as key if not already there
				# if int(proband) not in multiple_IR:
					# multiple_IR[proband]=[]
				# # loop through the list and add interpretation request to the list
				# [multiple_IR[proband].append(i[1]) for item in self.omicia_pilot if proband in item]
			
			# # then delete any probands with only one interpretation request
			# # loop through dict keys
			# for i in multiple_IR.keys():
				# # if less than 2 interpretation requests
				# if len(multiple_IR[i])<2:
					# # delete from dict
					# multiple_IR.pop(i)
			
			# #report findings
			# for i in multiple_IR:
				# print str(i)+" has multiple unblocked omicia interpretation requests: "  + ",".join(map(str,multiple_IR[i]))
			
			
			
			########################## Print the neg neg cases which could be rpeorted ################################
			#print str(len(self.negneg_pilot)) + " negative negative cases can be reported:"
			#print ",".join(self.negneg_pilot)


			########################## check for probands listed in spreadsheet from GEL team not in CIP-API #####################			
			# #print len(self.list_of_probands_in_spreadsheet)
			# missing_pilots=[]
			# # check for any cases not in CIP API
			# for i in self.list_of_probands_in_spreadsheet:
				# if str(i) not in map(str,self.pilot_count):
					# missing_pilots.append(i)
			# # # # # print self.pilot_count
			# print str(len(missing_pilots)) + " probands id in spreadsheet but not in CIP-API "
			# print missing_pilots
			
			########################## check for any cases in GEL spreadsheet which aren't in CIP-API ##############################
			# missing_pilots=[]
			# # # check for any cases not in CIP API
			# for i in self.all_gel_ids_in_spreadsheet:
				# if str(i) not in self.pilot_count:
					# missing_pilots.append(i)
			# # # print self.pilot_count
			# print str(len(missing_pilots)) + " probands id in self.all_gel_ids_in_spreadsheet but not in CIP-API "
			# #print missing_pilots
			
			# ############################ check for any cases in API which aren't on the referring clinician spreadsheet ###########################
			# cant_report=[]
			# # check for any cases in CIP API where we don't have the clinician info
			# for i in set(self.pilot_count):
				# if str(i) not in map(str,self.spreadsheet_with_referring_clinician_info):
					# cant_report.append(i)
			# print str(len(cant_report)) + " probands in CIP-API but not in self.all_gel_ids_in_spreadsheet"
			# print cant_report
			
			
			
	def read_interpretation_request(self,url):
		# pass the url to the function which reads the url. assign to interpretation_request
		interpretation_request=self.read_API_page(url)
		
		# loop through each report to find the highest cip_version
		for j in range(len(interpretation_request["interpreted_genome"])):
			# if the cip version is greater than that already seen
			if int(interpretation_request["interpreted_genome"][j]["cip_version"])>self.max_cip_ver:
				# record the max cip version
				self.max_cip_ver=interpretation_request["interpreted_genome"][j]["cip_version"]
		
		#set flag to mark this case as positive or negative
		positive=False
		
		#set flag to enable any troublesome cases to be ignored
		ignore=False
		
		# check tiered variants exists (one or two cases don't have this in the API)
		if 'TieredVariants' not in interpretation_request['interpretation_request_data']['json_request']:
			#set ignore == true
			ignore=True
			
		# see if there are any tiered variants (these are in a list)
		else:
			for variant in interpretation_request['interpretation_request_data']['json_request']['TieredVariants']:
				# there can be a list of classifications for a variant eg if the gene is in multiple panels. 
				# loop through these incase one panel has a different tier to the others
				for i in range(len(variant['reportEvents'])):
					# Look for tier1 and tier2 variants (ignore tier3)
					if variant['reportEvents'][i]['tier'] in ["TIER1","TIER2"]:
						# if present mark case as positive 
						positive=True
		
		# next look at CIP candidate variants, but no need to look if case already has tier1 or tier2 variant
		if positive or ignore:
			pass
		else:
			# loop through the interpreted_genome, looking for the one with highest cip version
			for interpreted_genome in interpretation_request['interpreted_genome']:
				# if it's the highest cip version
				if interpreted_genome['cip_version'] == self.max_cip_ver:
					# check if there are any variants.
					if len(interpreted_genome['interpreted_genome_data']['reportedVariants']) > 0:
						#mark proband as positive
						positive=True
		
		#if a tier1 or 2 variant has been seen add probandid to the dict
		if positive:
			self.negpos_pilot.append(self.proband)
		elif ignore:
			self.undetermined_pilot.append(self.proband)
		#otherwise add to the negative dict
		else:
			self.negneg_pilot.append(self.proband)
		
		# reset max_cip_version
		self.max_cip_ver = 0
		
if __name__=="__main__":
	c=connect()
	c.build_url()
