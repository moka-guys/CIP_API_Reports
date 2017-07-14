list_of_GELIDS=('112000100','112000592','112000896','50004237','50003018','50002021','50003754','50001871','50002442','50001829','50002721','50003319','50002422','50003808','50004182','50004719','50004176','50003510','50003586','50004205','50002771','50002774','50003773','50003587','50004058')

bash_script_path="/home/mokaguys/Documents/GeL_reports/170713.sh"
bash_script=open(bash_script_path,'w')
bash_script.write("source activate pyODBC\n")
for ID in list_of_GELIDS:
	bash_script.write("python ~/Apps/CIP_API/gel_report.py -g %s -h False\n" % ID)
bash_script.close()