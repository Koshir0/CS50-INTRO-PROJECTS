from sys import argv, exit
import csv
import cs50

if len(argv) != 2:
	print("YOU SHOULD ENTER THE HOUSE")
	exit(1)
house = argv[1]
# print(house)

db = cs50.SQL("sqlite:///students.db")

students = db.execute("SELECT * FROM students where house =?", house)



for student in sorted(students, key=lambda item: item['last']):
	if student['middle'] == "NULL":
			print(f"{student['first']} {student['last']}, born {student['birth']}")
	else:
		print(f"{student['first']} {student['middle']} {student['last']}, born {student['birth']}")