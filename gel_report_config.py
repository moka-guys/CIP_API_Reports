
####################### Authentication ##################
# path to files containing
username =  "/home/mokaguys/Apps/CIP_API/auth_username.txt"
pw = "/home/mokaguys/Apps/CIP_API/auth_pw.txt"

####################### Requests module ##################
#the proxy settings for requests module
proxy={'http':'proxy.gstt.local:80'} # if proxy is not required remove/comment this line do not leave blank

################# report modifications #####################
# New organisation name - only used to create the new_header_line below (no longer in use))
org_name="Viapath"
# New line for header
# new_header_line="This report has been generated by "+org_name+" using data obtained from the Genomics England APIs." # no longer needed
new_header_line=""

# Where the patient information template can be found
new_table="/home/mokaguys/Apps/CIP_API/patient_info_table_template.html"

# What colour do you want to change the header banner to?
new_banner_colour="#c497c2"

# what logo do you want to replace the gel logo with?
new_logo="/home/mokaguys/Apps/CIP_API/images/viapathlogo_white.png"

########################### pdfkit ##########################
# path to the wkhtmltopdf executable
wkhtmltopdf_path="/home/mokaguys/Apps/wkhtmltox/bin/wkhtmltopdf"


########################### Report location #################
# Where do you want the outputs?
html_reports="/home/mokaguys/Documents/GeL_reports/html/" # intermediate html files
pdf_dir="/home/mokaguys/Documents/GeL_reports/"