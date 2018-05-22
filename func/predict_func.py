# -*- coding: utf-8 -*-
"""
Created on 2018/5/20 

@author: susmote
"""
import urllib
import requests
import urllib.request
import numpy as np
from PIL import Image
from sklearn.externals import joblib
import os


def verify(url, model):
    """
    :param url: 验证码地址
    :param save: 是否保存临时文件到cache
    :return:
    """
    i = 0
    file_list = os.listdir('cache/')
    for file in file_list:
        file_name = os.path.splitext(file)[0]
        if file_name != ".DS_Store" and file_name != "captcha":
            if i == int(file_name):
                i = int(file_name)+1
            if i < int(file_name):
                i = int(file_name)
    print(i)
    session = requests.session()
    r = session.get(url)
    print(r)
    path = 'cache/'
    with open(path+ 'captcha.png', 'wb') as f:
        f.write(r.content)
    with open( path + '%s.png'%(i), 'wb') as f:
        f.write(r.content)
    image = Image.open( path +'captcha.png')
    x_size, y_size = image.size
    y_size -= 5

    # y from 1 to y_size-5
    # x from 4 to x_size-18
    piece = (x_size-24) / 8
    centers = [4+piece*(2*i+1) for i in range(4)]
    data = np.empty((4, 21 * 16), dtype="float32")
    for i, center in enumerate(centers):
        single_pic = image.crop((center-(piece+2), 1, center+(piece+2), y_size))
        data[i, :] = np.asarray(single_pic, dtype="float32").flatten() / 255.0
    clf = joblib.load(model)
    answers = clf.predict(data)
    answers = map(chr, map(lambda x: x + 48 if x <= 9 else x + 87 if x <= 23 else x + 88, map(int, answers)))
    return answers


# def save_code():


