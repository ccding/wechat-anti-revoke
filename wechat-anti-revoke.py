#!/usr/bin/env python
# -*-encoding:utf-8-*-

import sys
reload(sys)
sys.setdefaultencoding('UTF8')

import os, re, shutil, time, collections, json

import itchat
from itchat.content import *

msg_store = collections.OrderedDict()
timeout = 600
sending_type = {'Picture': 'img', 'Video': 'vid'}

def clear_timeouted_message():
    now = time.time()
    count = 0
    for k, v in msg_store.items():
        if now - v['ReceivedTime'] > timeout:
            count += 1
        else:
            break
    for i in range(count):
        item = msg_store.popitem(last=False)

def get_sender_receiver(msg):
    sender = None
    receiver = None
    if msg['FromUserName'][0:2] == '@@': # group chat
        sender = msg['ActualNickName']
        m = itchat.search_chatrooms(userName=msg['FromUserName'])
        if m is not None:
            receiver = m['NickName']
    elif msg['ToUserName'][0:2] == '@@': # group chat by myself
        sender = msg['ActualNickName']
        m = itchat.search_chatrooms(userName=msg['ToUserName'])
        if m is not None:
            receiver = m['NickName']
    else: # personal chat
        m = itchat.search_friends(userName=msg['FromUserName'])
        if m is not None:
            sender = m['NickName']
        m = itchat.search_friends(userName=msg['ToUserName'])
        if m is not None:
            receiver = m['NickName']
    return sender, receiver

def print_msg(msg):
    print json.dumps(msg).decode('unicode-escape').encode('utf8')

def get_whole_msg(msg):
    sender, receiver = get_sender_receiver(msg)
    if len(msg['FileName']) > 0 and len(msg['Url']) == 0:
        msg['Text'](msg['FileName'])
        c = '@%s@%s' % (sending_type.get(msg['Type'], 'fil'), msg['FileName'])
        return ['[%s]->[%s]:' % (sender, receiver), c]
    c = msg['Text']
    if len(msg['Url']) > 0:
        c += ' ' + msg['Url']
    return ['[%s]->[%s]: %s' % (sender, receiver, c)]

@itchat.msg_register([TEXT, PICTURE, MAP, CARD, SHARING, RECORDING,
    ATTACHMENT, VIDEO, FRIENDS], isFriendChat=True, isGroupChat=True)
def normal_msg(msg):
    print_msg(get_whole_msg(msg))
    now = time.time()
    msg['ReceivedTime'] = now
    msg_id = msg['MsgId']
    msg_store[msg_id] = msg
    clear_timeouted_message()

@itchat.msg_register([NOTE], isFriendChat=True, isGroupChat=True)
def note_msg(msg):
    print_msg(get_whole_msg(msg))
    if re.search(r'<sysmsg type="revokemsg">', msg['Content']) != None:
        old_msg_id = re.search("\<msgid\>(.*?)\<\/msgid\>", msg['Content']).group(1)
        old_msg = msg_store.get(old_msg_id)
        if old_msg is None:
            return
        msg_send = get_whole_msg(old_msg)
        for m in msg_send:
            itchat.send(m, toUserName='filehelper')
        clear_timeouted_message()

if __name__ == '__main__':
    itchat.auto_login(hotReload=True, enableCmdQR=2)
    itchat.run()
