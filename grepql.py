'''
grepql.py

Encoding: UTF-8

Warning: This script uses root account in mysql. Be sure to edit user for respective use.

License: GPL v3
@author: Noirdemort
'''

import mysql.connector as myc
from contextlib import ContextDecorator
import argparse
import os
import subprocess
from beautifultable import BeautifulTable
from getpass import getpass

class MySQLizer(ContextDecorator):
	'''
		Context Wrapper Class
		Sets up and tears down connection
	'''
	
	def __init__(self, db):
		self.db = db

	def __enter__(self):
		print("[*] Initializing connection...")
		user = os.environ.get("MySQL_USER")
		if not user:
			user = input("[*] Enter MySQL user: ")
		pwd = os.environ.get("MySQL_SECRET")
		if not pwd:
			pwd = getpass(f"[*] Enter MySQL password for {user}:")
		self.cnx = myc.connect(host="localhost", user=user, passwd=pwd, database=self.db)
		self.cursor = self.cnx.cursor()
		print("[+] Established connection with cursor.")
		return self

	def __exit__(self, *exc):
		print("\n[*] Initiating termination protocols...")
		self.cursor.close()
		self.cnx.close()
		print("[+] Cursor closed.")
		print("[+] Connection closed.")		
		return False


parser = argparse.ArgumentParser(prog='GrepQL', description="GrepQL: Grep-ing SQL Databases")
parser.add_argument('--db', help="Database Name", required=True)
parser.add_argument('--table', help="Table in Database (Optional)")
parser.add_argument('--search', help="grep like search query", required=True)

args = parser.parse_args()

tables = []
if args.table:
	tables.append(args.table)

print(f"\nArgs: {args}\n")


with MySQLizer(args.db) as dbc:

	if not tables:
		# fill table when none provided
		dbc.cursor.execute("show tables;")
		for tname in dbc.cursor:
			tables.append(tname[0])
	
	for table in tables:
		print(f"\n[*] Processing Records for table: {table}")
		dbc.cursor.execute(f"desc {table};")
		
		print("#$> Table Description:")
		# Setting table headers and formatting
		tabp = BeautifulTable()
		tabp.column_headers = ["Field", "Type", "Null", "Key", "Default", "Extra"]
		tabp.column_alignments['Field'] = BeautifulTable.ALIGN_LEFT
		tabp.column_alignments['Type'] = BeautifulTable.ALIGN_LEFT
		tabp.column_alignments['Null'] = BeautifulTable.ALIGN_LEFT
		for des in dbc.cursor:
			tabp.append_row(des)
		print(tabp)
		print()

		dbc.cursor.execute(f"select * from {table};")
		for record in dbc.cursor:
			term = ' '.join(record).lower()
			# Using real grep here
			found = subprocess.getoutput(f"echo {term} | grep {args.search}")
			if found:
				print(f"Matches >> {record}")

