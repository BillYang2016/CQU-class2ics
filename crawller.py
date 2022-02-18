# coding: utf-8
# !/usr/bin/python

import sys
import requests
import json

stuid = '' # 请填入学号

headers = {
	'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
	'Host': 'my.cqu.edu.cn',
	'Referer': 'http://my.cqu.edu.cn/enroll/CourseStuSelectionList',
	'Accept': 'application/json, text/plain, */*',
	'Accept-Encoding': 'gzip, deflate',
	'Connection': 'keep-alive',
	'Authorization': '',  # 填入 Bearer Token
	'Cookie': ''  # 填入 Cookie
}


def getCourseTime(encryptedCourseId):  # 通过课程加密名称获取已选课程信息
	url = 'http://my.cqu.edu.cn/enroll-api/enrollment/courseDetails/'+encryptedCourseId+'?selectionSource=%E4%B8%BB%E4%BF%AE'

	body = requests.get(url, headers=headers)  # 完成假访问
	courseTable = json.loads(body.text)

	classes = courseTable['selectCourseListVOs'][0]['selectCourseVOList']
	
	i = 0
	while(i < len(classes)):
		if classes[i]['selectedFlag'] is True:  # 找到选课
			return classes[i]
		i += 1


def printJson(courseName, instructorName, courseDetails):
	dic1 = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '日': 7}
	timestr = courseDetails['teachingWeekFormat']
	times = timestr.split(',')

	global classTimejson, errors, classInfoArray

	i = 0
	while(i < len(times)):  # 对于每个课程时间单独处理
		if(times[i].find('-') != -1):
			startWeek = times[i].partition('-')[0]
			endWeek = times[i].partition('-')[2]
		else:
			startWeek = endWeek = times[i]
		if(courseDetails['weekDayFormat'] == ''):
			return False
		else:
			weekday = dic1[courseDetails['weekDayFormat']]
		classroom = courseDetails['roomName']
		
		j = 0
		classTime = -1
		while(j < len(classTimejson['classTime'])):  # 获取json中对应编号
			if(courseDetails['periodFormat'] == classTimejson['classTime'][j]['name']):
				classTime = j
			j += 1

		if(classTime == -1):
			print('检测到未配置的课程时间：' + courseDetails['periodFormat'] + '小节，请在 conf_classTime.json 中进行配置')
			errors += 1
		else:
			classTime += 1

		timeMap = {}
		timeMap['startWeek'] = int(startWeek)
		timeMap['endWeek'] = int(endWeek)

		classMap = {}
		classMap['className'] =  courseName + ' ' + instructorName  # 课程名 + 导师名
		classMap['week'] = timeMap  # 开始结束周
		classMap['weekday'] = weekday  # 周几
		classMap['classTime'] = classTime  # 上课时间
		classMap['classroom'] = classroom  # 教室
		# sheet1.write(row, 4, 3)  # 单数双数周（暂无用）
		
		classInfoArray.append(classMap)

		i += 1
	return True


if __name__ == '__main__':
	url = 'http://my.cqu.edu.cn/api/enrollment/timetable/student/' + stuid

	body = requests.get(url, headers=headers)  # 完成假访问
	courses = json.loads(body.text)

	global classTimejson, errors, classInfoArray
	
	classInfoArray = []

	with open(sys.path[0] + '/conf_classTime.json', 'r', encoding='UTF-8') as jsonfile:
		classTimejson = json.load(jsonfile)

	i = 0
	lasting = 1
	lastID = 0
	while i < len(courses['data']):
		courseDetails = courses['data'][i]
		courseName = courseDetails['courseName']
		instructorName = courseDetails['classTimetableInstrVOList'][0]['instructorName']
		courseID = courseDetails['id']
		originName = courseName
		
		if courseDetails['classType'] != '理论':
			courseName = courseName + courseDetails['classType']
		
		if lastID == courseID:
			lasting += 1
		else:
			lasting = 1
		
		if lasting == 1:
			print('已获取课程 ' + originName + ' 导师名: ' + instructorName + ' 与课程时间地点')
		
		status = printJson(courseName, instructorName, courseDetails) # 获取信息填充Json
		
		if lasting == body.text.count("\"id\":\"" + str(courseID) + "\""):
			if status is True:
				print('已储存课程信息\n')
			else:
				print('课程信息不全，已跳过\n')
		
		i += 1
		lastID = courseID

	map = {}
	map['classInfo'] = classInfoArray
	
	with open(sys.path[0] + '/conf_classInfo.json', 'w', encoding = 'gb2312') as f:
		f.write(json.dumps(map, ensure_ascii = False))
		f.close()
	
	print('已导出json\n')
