from sys import argv, exit
import csv
import cs50

if len(argv) != 2:
	print("missing command-line arguments")
	exit(1)
csvfile = argv[1]
# print(csvfile)

open(f"students.db", "w").close()
db = cs50.SQL("sqlite:///students.db")



db.execute("CREATE TABLE students (first TEXT, middle TEXT, last TEXT, house TEXT, birth NUMERIC)")

with open(csvfile, "r") as houses:
	reader = csv.DictReader(houses)
	for row in reader:
		wholeName = row["name"].split(" ")
		if len(wholeName) == 3:
			first  = wholeName[0]
			middle = wholeName[1]
			last   = wholeName[2]
		else:
			first  = wholeName[0]
			middle = "NULL"
			last   = wholeName[1]

		db.execute("INSERT INTO students (first, middle, last, house, birth) VALUES(?, ?, ?, ?, ?)",
                               first, middle, last, row["house"], row["birth"])