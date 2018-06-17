# -*- coding: utf-8 -*-
"""
Created on 2018/5/22

@author: susmote
"""

from flask import Flask, jsonify, abort, make_response, request
from func.get_operate_link import get_operate_link
from func.crawl_func import get_timetable_dic, get_Grade, get_student_info
import urllib.parse
import requests
from bs4 import BeautifulSoup
from PIL import Image
import numpy as np
from sklearn.externals import joblib
import os

app = Flask(__name__)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': '页面没有找到'}), 404)


@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify({'error': '参数不全'}), 400)


@app.route('/stu/api/v1.0/tables',  methods=["GET", "POST"])
def get_tables():
    if not request.values or request.values['student_id'] == '' or request.values['password'] == '':
        abort(400)
    student_id = request.values['student_id']
    password = request.values['password']
    host = "125.221.35.100"
    url = 'http://' + host + "/" + 'default2.aspx'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
        'Referer': url,
        'Host': host
    }
    while True:
        session = requests.session()

        # 获取标识码
        soup = BeautifulSoup(session.get(url, headers=headers).text, 'lxml')
        __VIEWSTATE = soup.find_all('input', type="hidden")[0]['value']

        captcha_url = 'http://' + host + "/" + 'CheckCode.aspx'
        r = session.get(captcha_url, headers=headers)
        path = 'cache/'
        with open(path + 'captcha.png', 'wb') as f:
            f.write(r.content)
        image = Image.open(path + 'captcha.png')
        x_size, y_size = image.size
        y_size -= 5
        piece = (x_size - 24) / 8
        centers = [4 + piece * (2 * i + 1) for i in range(4)]
        data = np.empty((4, 21 * 16), dtype="float32")
        for i, center in enumerate(centers):
            single_pic = image.crop((center - (piece + 2), 1, center + (piece + 2), y_size))
            data[i, :] = np.asarray(single_pic, dtype="float32").flatten() / 255.0
        clf = joblib.load('model/SVC_Model_zf.pkl')
        answers = clf.predict(data)
        answers = map(chr, map(lambda x: x + 48 if x <= 9 else x + 87 if x <= 23 else x + 88, map(int, answers)))
        check_code = ''.join(list(answers))

        # 封装需要post的数据
        postdata = {
            "__VIEWSTATE": __VIEWSTATE,
            "TextBox1": student_id,
            "TextBox2": password,
            "TextBox3": check_code,
            "Button1": "",
            'RadioButtonList1': '\xd1\xa7\xc9\xfa',
            'Button1': '',
        }

        res = session.post(url, data=postdata, headers=headers)
        if '验证码不正确' in res.text:
            continue

        if '密码错误' in res.text or '用户名不存在' in res.text:
            return jsonify({'error': "你输入的学号或密码不正确"})
        else:
            # 登录成功后，返回的是你教务系统的主页源代码
            r = session.get('http://' + host + "/" + 'xs_main.aspx?xh=' + student_id, headers=headers)
            link_dic = get_operate_link(host, r.text)
            print(list(link_dic))

            # 获取学生个人课表和个人信息
            student_class = session.get(link_dic['学生个人课表'], headers=headers)
            stu_info = get_student_info(student_class.text)
            for i in range(len(list(stu_info.keys()))):
                print(list(stu_info.keys())[i], ':', stu_info[list(stu_info.keys())[i]])
            stu_timetable = get_timetable_dic(student_class.text)
            return jsonify({'stu_info': stu_info, 'stu_timetable': stu_timetable})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
