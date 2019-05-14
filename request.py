import requests

response = requests.get('https://unlockitsocketapp.herokuapp.com/api/simple/students/' + str(20451313))

serialNum = 3

print(response.json())
#for entry in response.json():
#    if entry['serial_number'] == 3:
#        print(entry['student_number'])
