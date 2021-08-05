# coding: utf-8
# !/usr/bin/python

import sys
import requests
import json
import xlwt

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


def printExcel(courseName, instructorName, courseDetails):
	dic1 = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '日': 7}
	timestr = courseDetails['teachingWeekFormat']
	times = timestr.split(',')

	global f, sheet1, row, classTimejson, errors

	i = 0
	while(i < len(times)):  # 对于每个课程时间单独处理
		row += 1
		if(times[i].find('-') != -1):
			startWeek = times[i].partition('-')[0]
			endWeek = times[i].partition('-')[2]
		else:
			startWeek = endWeek = times[i]
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

		sheet1.write(row, 0, courseName + ' ' + instructorName)  # 课程名 + 导师名
		sheet1.write(row, 1, startWeek)  # 开始周
		sheet1.write(row, 2, endWeek)  # 结束周
		sheet1.write(row, 3, weekday)  # 周几
		sheet1.write(row, 4, 3)  # 单数双数周（暂无用）
		sheet1.write(row, 5, classTime)  # 上课时间
		sheet1.write(row, 6, classroom)  # 教室

		i += 1


def processDetails(courseDetails):
	
	if courseDetails['childrenList'] is not None:  # 有实验课
		print('课程包含实验课，正在处理实验课信息')
		printExcel(courseName+'实验', courseDetails['childrenList'][0])


if __name__ == '__main__':
	url = 'http://my.cqu.edu.cn/api/enrollment/timetable/student/' + stuid

	body = requests.get(url, headers=headers)  # 完成假访问
	courses = json.loads(body.text)

	global f, sheet1, row, classTimejson, errors
	f = xlwt.Workbook()
	sheet1 = f.add_sheet(u'sheet1', cell_overwrite_ok=True)  # 创建Excel
	row0 = [u'className', u'startWeek', u'endWeek', u'weekday', u'week', u'classTime', u'classroom']
	row = 0

	for i in range(0, len(row0)):  # 第一行
		sheet1.write(0, i, row0[i])

	with open(sys.path[0] + '/conf_classTime.json', 'r', encoding='UTF-8') as jsonfile:
		classTimejson = json.load(jsonfile)

	i = 0
	lasting = 1
	lastID = 0
	while(i < len(courses['data'])):
		courseDetails = courses['data'][i]
		courseName = courseDetails['courseName']
		instructorName = courseDetails['classTimetableInstrVOList'][0]['instructorName']
		courseID = courseDetails['id']
		
		if(courseDetails['classType'] != '理论'):
			courseName = courseName + courseDetails['classType']
		
		if(lastID == courseID):
			lasting += 1
		else:
			lasting = 1
		
		if(lasting == 1):
			print('已获取课程 ' + courseName + ' 导师名: ' + instructorName + ' 与课程时间地点')
		
		printExcel(courseName, instructorName, courseDetails)  # 获取信息填充Excel
		
		if(lasting == body.text.count("\"id\":\"" + str(courseID) + "\"")):
			print('已储存课程信息\n')
		
		i += 1
		lastID = courseID

	f.save('classInfo.xls')