#! /usr/bin/env python
# -*- coding: utf-8 -*-

import rospy
import roslib
from std_msgs.msg import String
from std_msgs.msg import Int8
from sound_play.libsoundplay import SoundClient
import os
import sys
import time
import wave

class speech_control():
    def __init__(self):
        self.musicPath = '/home/keaixin/catkin_ws/src/homework/sounds/youbelongwithme.mp3'
        self.question_start_signal = "~/home/keaixin/catkin_ws/src/homework/sounds/question_start_signal.wav"
        # Initialize sound client
        self.sh = SoundClient(blocking = True)
        #self.voice = rospy.get_param("~voice", "voice_don_diphone")
        self.voice = rospy.get_param("~voice", "voice_kal_diphone")
        rospy.sleep(1)
        self.sh.stopAll()
        rospy.sleep(1)
        self.tuling_res = None
        self.baiducallback_string = None
        self.is_answer_question = False
        # Publisher topics
        self.pub_to_tuling_topic_name = rospy.get_param("pub_to_tuling_topic_name " , "/tuling_topic")
        self.tuling_pub  = rospy.Publisher(self.pub_to_tuling_topic_name, String, queue_size=1)
        self.pub_to_tur_control = rospy.get_param("pub_to_tur_control" , "voiceWords")
        self.tur_control_pub = rospy.Publisher(self.pub_to_tur_control,  String, queue_size=1)

        # Subscriber topics
        self.sub_baidu_back_topic_name = rospy.get_param("sub_baidu_back_topic_name" , "/my_voice")
        rospy.Subscriber(self.sub_baidu_back_topic_name, String, self.baiduCallback)
        self.sub_tuling_response_topic_name = rospy.get_param("sub_tuling_response_topic_name" , "/tuling_translate_result")
        rospy.Subscriber(self.sub_tuling_response_topic_name, String, self.tulingCallback)
        

    def tulingCallback(self, msg):
        self.tuling_res = msg.data

    def baiduCallback(self, msg):
        self.baiducallback_string = msg.data
        if msg.data.strip()=='':
            self.sh.say("sorry I did not clearly hear you", self.voice)
            self.sh.say("could you say it again, please", self.voice)
            self.is_answer_question = False
        else:
            string = msg.data
            print ("[your question]:",string)
            symbols = ["!", "?", ".", ",", ";", ":"]
            output = []
            if string[-1] in symbols:
                string = string[:-1]
            for part in string.lstrip().split(","):
                for word in part.split():
                    for symbol in symbols:
                        if symbol in word:
                            word = word[:-1]
                    output.append(word)
            output = [item.lower() for item in output]
            #print (output)
            
            if "failed" in output:
                self.sh.say("sorry I did not clearly hear you", self.voice)
                self.sh.say("could you say it again, please", self.voice)
                os.system('rostopic pub -1 /kws_data std_msgs/String "jack" ')
                self.is_answer_question = False
            
            elif "hi" in output or "hello" in output or "hey" in output:
                if "time" in output:
                    self.sh.say("Are you asking me the time now", self.voice)          
                    self.tuling_pub.publish("现在几点了")
                    rospy.sleep(2)
                    print ("[jack's answer]:",self.tuling_res)
                    self.sh.say(str(self.tuling_res), self.voice)
                elif "weather" in output:
                    self.sh.say("Are you asking me about the weather today", self.voice)          
                    self.tuling_pub.publish("今天天津天气")
                    rospy.sleep(1)
                    print ("[jack's answer]:",self.tuling_res)
                    self.sh.say(str(self.tuling_res), self.voice)
                elif "joke" in output:
                    self.sh.say("ok I will tell you a joke", self.voice)
                    self.tuling_pub.publish("讲一个笑话吧")
                    rospy.sleep(1)
                    print ("[jack's answer]:",self.tuling_res)
                    self.sh.say(str(self.tuling_res), self.voice)           
                elif "story" in output or "sorry" in output:
                    self.sh.say("ok I will tell you a story", self.voice)
                    self.tuling_pub.publish("讲一个故事吧")
                    rospy.sleep(1)
                    print ("[jack's ansewer]:",self.tuling_res)
                    self.sh.say(str(self.tuling_res), self.voice)
                elif "milk" in output or "music" in output:
                    self.sh.say("ok I will put a short piece of music for you", self.voice)
                    print("[jack's answer]:ok I will put a short piece of music for you")
                    print('playing music...')
                    self.sh.playWave(self.musicPath)
                    self.sh.say("that's all, do you like it", self.voice)
                    print("[jack's answer]:that's all, do you like it")
                    rospy.sleep(5)
                    os.system('rostopic pub -1 /voiceWakeup std_msgs/String "ok" ')

            elif self.is_answer_question is False:
                if ("dog" in output or "photo" in output or "go" in output or "out" in output or "back" in output):
                    if "want" in output or "i" in output or "to" in output or "i'll" in output or "leave" in output or string == "i want to go":
                        self.sh.say("i heard that you want to go, all right, i'm ready", self.voice)
                        self.tur_control_pub.publish("go")
                        print("[jack's answer]: i heard that you want to go, all right, i'm ready")
                        rospy.sleep(5)
                        os.system('rostopic pub -1 /voiceWakeup std_msgs/String "ok" ')
                        self.is_answer_question = False
                    elif "out" in output or "let's" in output or "door" in output or "dog" in output or string == "let's go out":
                        self.sh.say("ok let's go to the taxi", self.voice)
                        self.tur_control_pub.publish("out")
                        print("[jack's answer]: ok let's go to the taxi")
                        rospy.sleep(5)
                        os.system('rostopic pub -1 /voiceWakeup std_msgs/String "ok" ')
                        self.is_answer_question = False
                    elif "back" in output or "you" in output or string == "you can go back":
                        self.sh.say("ok, wish you a good trip, goodbye", self.voice)
                        self.tur_control_pub.publish("back")
                        print("[jack's answer]: ok, wish you a good trip, goodbye")
                        #rospy.sleep(5)
                        #os.system('rostopic pub -1 /voiceWakeup std_msgs/String "ok" ')
                        self.is_answer_question = False
                else:
                    self.sh.say("sorry I did not clearly hear you", self.voice)
                    self.sh.say("could you say it again, please", self.voice)
                    os.system('rostopic pub -1 /voiceWakeup std_msgs/String "jack" ')
            
            self.answer_question(output)

    def answer_question(self, output):
        self.sh.stopAll()
        if self.is_answer_question == True:
            if "time" in output:
                self.sh.say("Are you asking me the time now", self.voice)          
                self.tuling_pub.publish("现在几点了")
                rospy.sleep(1)
                print self.tuling_res
                self.sh.say(str(self.tuling_res), self.voice)
            elif "weather" in output:
                self.sh.say("Are you asking me about the weather today", self.voice)          
                self.tuling_pub.publish("今天天津天气")
                rospy.sleep(1)
                print self.tuling_res
                self.sh.say(str(self.tuling_res), self.voice)
            elif "joke" in output:
                self.sh.say("ok I will tell you a joke", self.voice)
                self.tuling_pub.publish("讲一个笑话吧")
                rospy.sleep(1)
                print self.tuling_res
                self.sh.say(str(self.tuling_res), self.voice)           
            elif "story" in output or "sorry" in output:
                self.sh.say("ok I will tell you a story", self.voice)
                self.tuling_pub.publish("讲一个故事吧")
                rospy.sleep(1)
                print self.tuling_res
                self.sh.say(str(self.tuling_res), self.voice)
            elif "milk" in output or "music" in output:
                self.sh.say("ok I will put a short piece of music for you", self.voice)
                print('playing music')
                self.sh.playWave(self.musicPath)
                self.sh.say("that's all, do you like it", self.voice)

if __name__ == '__main__':
    rospy.init_node("speech_control")
    ctrl = speech_control()
    rospy.spin()