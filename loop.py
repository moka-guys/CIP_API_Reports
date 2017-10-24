# list of probands
list_of_GELIDS=['50003384', '50001343', '50004169', '50002418', '50004234', '50003398', '50002250', '50004174', '50004235', '50004232', '50002730', '50002721', '50003319', '50002422', '50003799', '50003808', '50004024', '50004026', '50004182', '50004661', '50004719', '50002560', '50003506', '50003796', '50003807', '50003810', '50004176', '50003587', '50002771', '50004237', '50003510', '50003515', '50003586', '50004205', '50002774', '50003318', '50003773', '50004058', '50003507', '50003018', '50002021', '50003754', '50003516', '50001871', '50002442', '50001829', '50002045', '50002423', '50002040', '50004022', '50003388', '50004203', '50003760', '50002020', '50004011', '50002249', '50003554', '50003385', '50003382', '50002554', '50001828', '50004185', '50003316', '50003583', '50002421']

#set the path to the script we want to use to generate the report
script_path= "/home/mokaguys/Documents/CIP_API_development/gel_report.py"
script_path= "/home/mokaguys/Apps/CIP_API/gel_report.py"

#the bash script which we will write all the commands to.
bash_script_path="/home/mokaguys/Documents/GeL_reports/171024.sh"
bash_script=open(bash_script_path,'w')
bash_script.write("source activate pyODBC\n")
# add command for each proband
for ID in list_of_GELIDS:
	bash_script.write("python "+script_path+" -g %s -h True\n" % ID)
bash_script.close()