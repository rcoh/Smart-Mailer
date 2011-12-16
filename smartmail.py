#smartmail.py
#Copyright (C) 2011  Russell Cohen <rcoh@mit.edu>
#
#This file is part of Smart-Mailer.
#
#Smart-Mailer is free software: you can redistribute it
#and/or modify it under the terms of the GNU General Public License as
#published by the Free Software Foundation, either version 3 of the
#License, or (at your option) any later version.
#
#Smart-Mailer is distributed in the hope that it will be
#useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with Smart-Mailer.  If not, see
#<http://www.gnu.org/licenses/>.

import poplib
import smtplib
import moira
import time
import email # new statement
from email import parser

def get_new_messages():
  host = "pop.gmail.com"
  mail = poplib.POP3_SSL(host)
  mail.getwelcome()
  mail.user("mitsmartmail@gmail.com")
  mail.pass_("raptor-mail")

  numMessages = len(mail.list()[1])
  messages = []
  for i in range(numMessages):
      message = '\n'.join(mail.retr(i+1)[1])
      messages.append(parser.Parser().parsestr(message)) #new statement

  mail.quit()
  return messages

ADD = 0
REMOVE = 1
INTERSECT = 2
def process_message(message):
  target_expression = message['Delivered-To'].split('+')[-1].split('@')[0].split('.')
  send_targets = process_target(target_expression) 
  del message['Delivered-To']
  message['cc'] = ','.join(list(send_targets))
  message['Reply-To'] = message['Delivered-To']
  fromaddr = message['From']
  toaddrs = list(send_targets)

  print 'target expression was: ', target_expression
  print 'we would send to: ', send_targets 
  send_msg(fromaddr, toaddrs, message)

def send_msg(fromaddr, toaddrs, message):
  import pdb; pdb.set_trace()
  server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
  #server = smtplib.SMTP_SSL('outgoing.mit.edu', 587)
  server.login('mitsmartmail@gmail.com', 'raptor-mail')
  server.set_debuglevel(1)
  server.sendmail(fromaddr, toaddrs, message.as_string())
  server.quit()

def process_target(target_expression):
  #work our way through the expression
  send_targets = set() 
  state = 0 
  for word in target_expression:
    if word == 'minus':
      state = 1
    elif word == 'intersect':
      state = 2
    elif state == 0:
      send_targets |= get_list_members(word)
    elif state == 1:
      if word in send_targets:
        send_targets -= set([word])
      else:
        send_targets -= get_list_members(word)
      state = 0
    elif state == 2:
      if word in send_targets:
        send_targets &= set([word])
      else:
        send_targets &= get_list_members(word)
  final_targets = []
  for adr in list(send_targets):
    if not '@' in adr:
      final_targets.append(adr + '@mit.edu')
    else:
      final_targets.append(ard)
  return final_targets 


def main_loop():
  while 1:
    print 'querying'
    messages = get_new_messages()
    start_moira()
    if messages:
      [process_message(m) for m in messages]
    time.sleep(10)

def start_moira():
  moira.connect()

def get_list_members(list_name, expanded_lists = []):
  try:
    members = moira.query('get_members_of_list', list_name)
    users = set([member['member_name'] for member in members if member['member_type'] in ['USER',
                                                                                          'STRING']])
    lists = set([member['member_name'] for member in members if member['member_type'] == 'LIST'])
    for mail_list in lists:
      if not mail_list in expanded_lists:
        users |= get_list_members(mail_list, expanded_lists + [list_name])
    return users
  except Exception: #TODO: fix
    return set()

if __name__ == "__main__":
  main_loop()
#  moira.connect()
#  print process_target(['523', 'minus', 'lalpert'])
