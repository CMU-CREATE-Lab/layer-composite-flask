from flask import Flask, jsonify, request, Response, make_response
import json
import os
import csv
import io
from flask_cors import CORS

#files will be formated as name_name1-start-end-type.csv

entries = os.listdir('./')
entries = [ entries for entries in entries if entries.endswith('.csv') ]
files = {}
#type = per
filesPerTenThousand = {}
#type = rate
filesPercent = {}
#type = number
filesNumber = {}
for x in entries:
	y = x.replace('.csv', '')
	arr = y.split('-')
	print(arr)
	files[arr[0]] = [int(arr[1]), int(arr[2]), x]
	if arr[3] == 'per':
		filesPerTenThousand[arr[0]] = x
	elif arr[3] == 'rate':
		filesPercent[arr[0]] = x
	else:
		filesNumber[arr[0]] = x

app = Flask(__name__)
cors = CORS(app)


def error_resp(msg):
	resp = jsonify(msg)
	resp.status_code = 400
	return resp
	
def get_min(layers):
	#returns the highest start date for the layers
	minimum = 'NAN'
	for x in layers:
		if minimum == 'NAN' or files[x][0] > minimum:
			minimum = files[x][0] 
	return minimum
	
def get_max(layers):
	#returns the lowest end date for the layers
	maximum = 'NAN'
	for x in layers:
		if maximum == 'NAN' or files[x][1] < maximum:
			maximum = files[x][1] 
	return maximum
	
def make_array(layers, minimum, maximum):
	#layers = files to combine
	#minimum = start year
	#maximum = end year
	#return = 2D array of combined layers
	title = ['Name'] + list(range(minimum, maximum+1))
	length = maximum - minimum
	toReturn = [title]
	fileNames = []
	for x in layers:
		name = files[x][2]
		fileNames.append(name)
	with open(fileNames[0], 'r') as csvfile: 
		csvreader = csv.reader(csvfile, delimiter=' ', quotechar='|')
		years = next(csvreader)[0].split(',')
		i = 1
		while int(years[i]) != minimum:
			i = i + 1
		mini = i
		maxi = i + (maximum - minimum)
		for row in csvreader:
			to_add = row[0].split(',')
			to_add = [to_add[0]] + to_add[mini:maxi+1]
			if len(to_add) > 1:
				toReturn.append(to_add)	
			else:
				toReturn.append(["NAN"])
	fileNames.pop(0)
	for x in fileNames:
		with open(x, 'r') as csvfile: 
			csvreader = csv.reader(csvfile, delimiter=' ', quotechar='|')
			index = 1
			years = next(csvreader)[0].split(',')
			i = 1
			while int(years[i]) != minimum:
				i = i + 1
			mini = i - 1
			for row in csvreader:
				data = row[0].split(',')
				if len(data) > 1 and toReturn[index][0] != "NAN":
					for num in range(1, len(toReturn[index])):
						toReturn[index][num] = float(toReturn[index][num]) + float(data[num + mini])
				else:
					toReturn[index] = ["NAN"]
				index = index + 1
	return toReturn
	
def get_average(file, fileNum):
	for row in range(1, len(file)):
		for col in range(1, len(file[row])):
			if file[row][col] != "NAN":
				print(file[row])
				file[row][col] = float(file[row][col]) / fileNum
	return file
	
@app.route('/')
def api_root():
	names = list(filesPerTenThousand.keys())
	return json.dumps({'criteria': names})
	
@app.route('/rate')
def api_rate():
	names = list(filesPercent.keys())
	return json.dumps({'criteria': names})
	
@app.route('/num')
def api_num():
	names = list(filesNumber.keys())
	return json.dumps({'criteria': names})
	
@app.route('/getcsv')
def api_getcsv():
	layers = request.args['files'].split(',')
	minimum = get_min(layers)
	maximum = get_max(layers)
	if minimum > maximum:
		msg = {"status":400, "message":"Malformed Request, bad date range: " + request.url}
		return error_resp(msg)
	arr = make_array(layers, minimum, maximum)
	dest = io.StringIO()
	writer = csv.writer(dest)
	for row in arr:
		writer.writerow(row)
	output = make_response(dest.getvalue())
	return output
	
@app.route('/getave')
def api_getave():
	layers = request.args['files'].split(',')
	minimum = get_min(layers)
	maximum = get_max(layers)
	if minimum > maximum:
		msg = {"status":400, "message":"Malformed Request, bad date range: " + request.url}
		return error_resp(msg)
	arr = make_array(layers, minimum, maximum)
	arr = get_average(arr, len(layers))
	dest = io.StringIO()
	writer = csv.writer(dest)
	for row in arr:
		writer.writerow(row)
	output = make_response(dest.getvalue())
	return output


@app.route('/getdates')
def api_getdates():
	layers = request.args['files'].split(',')
	minimum = get_min(layers)
	maximum = get_max(layers)
	if minimum > maximum:
		msg = {"status":400, "message":"Malformed Request, bad date range: " + request.url}
	else:
		msg = {"status":200, "message":"Correct date range"}
	
if __name__ == "__main__":
	app.run()