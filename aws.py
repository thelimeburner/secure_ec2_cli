#!/Users/lucasch/Library/Enthought/Canopy_64bit/User/bin/python
# Author: Lucas Chaufournier
# Date: June 3, 2016
#
#


import sys
from subprocess import Popen,PIPE
import os
import argparse
import getpass
import csv

#Run a command using subprocess
def runCMD(cmd):
	p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
	out,err = p.communicate()
	if p.returncode != 0:
		return err.rstrip(),True
	return out.rstrip(),False


def mvFile(fname,dest):
	#If none, then file wasnt supplied
	if fname == None:
		return True
	if os.path.exists(fname):
		res,err = runCMD("cp "+fname+" "+dest+"/.")
		if err:
			print err
			sys.exit(0)
		return True
	else:
		print "File "+fname+" Not Found!"
		sys.exit(0)




###FUNCTION TO ENCRYPT 
def encrypt(aws_home):
	global passwd
	cmd = "openssl aes-256-cbc -a -salt -in "+aws_home+"credentials -out "+aws_home+"credentials.enc -k "+passwd
	res,err = runCMD(cmd)
	if err:
		print "Error encrypting file: "
		print res
		sys.exit(0)
	#Remove original
	os.remove(aws_home+"credentials")
	return


###Function to Decrypt
def decrypt(aws_home):
	global passwd
	cmd = "openssl aes-256-cbc -d -a -in "+aws_home+"credentials.enc -out "+aws_home+"credentials -k "+passwd
	res,err = runCMD(cmd)
	if err:
		print "Error decrypting file: "
		print res
		sys.exit(0)
	return


##Function to parse CSV credentials
#Returns access,secret
def parseCSV(fname):
	with open(fname,'rb') as csvfile:
		reader = list(csv.reader(csvfile,delimiter=','))
		if len(reader)!= 2:
			print fname+" is not formatted correctly. Please provide the csv from amazon"
			sys.exit(0)
		return reader[1][1],reader[1][2]


##Function that creates the credentials file in ~/.aws/
def createCredFile(fname,aws_home):
	access,secret = parseCSV(aws_home+fname)
	f = open(aws_home+"credentials","w")
	f.write("[default]\n")
	f.write("aws_access_key_id="+access+"\n")
	f.write("aws_secret_access_key="+secret+"\n")
	f.close()


###FUNCTION THAT PRINT TRUE
def printTrue():
	print True
	return

##Function to get aws home dir
def getHome():
	#Get home directory
	home,err = runCMD("echo ~")
	if err:
		print "Error can not find home directory"
		print home
		sys.Exit(0)
	aws_dir = home+"/.aws/"
	return aws_dir

##Function to setup environment
def import_aws(cred,pub,priv):
	#Get home directory
	aws_dir = getHome()
	#Check if aws directory exists
	if not os.path.isdir(aws_dir):
		print "AWS DOES NOT EXIST"
		##Try to make directory, if already exists move on
		try:
			os.mkdir(aws_dir)
		except OSError:
			print '"AWS Already Exists'
	##Move cred to directory
	mvFile(cred,aws_dir)
	##Move pub to directory
	mvFile(pub,aws_dir)
	##Move priv to directory
	mvFile(priv,aws_dir)

	## Grab the name of the credentials csv
	file_path_parts =cred.split("/")
	fname = file_path_parts[len(file_path_parts)-1]

	##Create the credentials file in the aws_home_dir(~/.aws)
	createCredFile(fname,aws_dir)
	##Remove original
	os.remove(aws_dir+fname)
	encrypt(aws_dir)
	

	print "Import Complete! Your keys are now located in "+aws_dir
	return


def run_aws_command(cmd):
	global passwd
	aws_dir = getHome()
	decrypt(aws_dir)
	res, err = runCMD("aws "+cmd)
	print res
	##REmove plaintext file
	os.remove(aws_dir+"credentials")



parser = argparse.ArgumentParser()
parser.add_argument("--cred",type=str,help="[Requires -imp] Path of the credentials.csv file to use. Must be the amazon provide csv" )
parser.add_argument("--ssh_pub",type=str,help="[Requires -imp] Path of SSH Public Key to use",default=None)
parser.add_argument("--ssh_priv",type=str,help="[Requires -imp] Path of SSH Private Key to use",default=None)
parser.add_argument("-imp",help="[Requires -cred] Used to Import Keys",action="store_true")
parser.add_argument("-p",type=str,help="Specify the password to use for encrypt/decryption. Must be the first argument.")
parser.add_argument("configure",action="store_true")
parser.add_argument("args",nargs=argparse.REMAINDER)

args = parser.parse_args()



passwd = args.p


if args.imp:
	if not args.p:
		passwd = getpass.getpass(prompt="Please enter a password for encryption: ")
		verify = getpass.getpass(prompt="Verify Password: ")
		if passwd != verify:
			print "Passwords do not match. Please try again"
			sys.exit(0)
	if passwd is None:
		print "Password was not specified"
		sys.exit(0)
	#Check if credentials file provided 
	if args.cred:
		import_aws(args.cred,args.ssh_pub,args.ssh_priv)
	else:
		print "Please specify the path of the credentials.csv file to use"
else:
	if args.args[0] == "configure":
		print "Configure operation is not allowed"
		sys.exit(0)
	if not args.p:
		passwd = getpass.getpass(prompt="Please enter your encryption password: ")

	run_aws_command(" ".join(args.args))
