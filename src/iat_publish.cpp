/*
* 语音听写(iFly Auto Transform)技术能够实时地将语音转换成对应的文字。
*/

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include "qisr.h"
#include "msp_cmn.h"
#include "msp_errors.h"
#include "speech_recognizer.h"
#include <iconv.h>
#include"std_msgs/String.h"
#include "ros/ros.h"
#include "std_msgs/String.h"
#include<sound_play/SoundRequestActionGoal.h>
#define FRAME_LEN   640 
#define BUFFER_SIZE 4096
ros::Publisher pub;
int wakeupFlag   = 0 ;
int resultFlag   = 0 ;
ros::Publisher pub_voice;
void speak(std::string str)
{
    sound_play::SoundRequestActionGoal voice;
    voice.goal.sound_request.arg = str.c_str();
    voice.goal.sound_request.arg2 = "voice_kal_diphone";
    voice.goal.sound_request.sound = -3;
    voice.goal.sound_request.volume = 1.0;
    voice.goal.sound_request.command = 1;
    pub_voice.publish(voice);
}
static void show_result(char *string, char is_over)
{
    resultFlag=1;   
    printf("\rResult: [ %s ]", string);
    if(is_over)
        putchar('\n');
}

static char *g_result = NULL;
static unsigned int g_buffersize = BUFFER_SIZE;

void on_result(const char *result, char is_last)
{
    if (result) {
        size_t left = g_buffersize - 1 - strlen(g_result);
        size_t size = strlen(result);
        if (left < size) {
            g_result = (char*)realloc(g_result, g_buffersize + BUFFER_SIZE);
            if (g_result)
                g_buffersize += BUFFER_SIZE;
            else {
                printf("mem alloc failed\n");
                return;
            }
        }
        strncat(g_result, result, size);
        show_result(g_result, is_last);
    }
}

void on_speech_begin()
{
    if (g_result)
    {
        free(g_result);
    }
    g_result = (char*)malloc(BUFFER_SIZE);
    g_buffersize = BUFFER_SIZE;
    memset(g_result, 0, g_buffersize);

    printf("Start Listening...\n");
    
   
}
void on_speech_end(int reason)
{
    if (reason == END_REASON_VAD_DETECT)
        printf("\nSpeaking done \n");
    else
        printf("\nRecognizer error %d\n", reason);
}

/* demo recognize the audio from microphone */
static void demo_mic(const char* session_begin_params)
{
    int errcode;
    int i = 0;

    struct speech_rec iat;

    struct speech_rec_notifier recnotifier = {
        on_result,
        on_speech_begin,
        on_speech_end
    };

    errcode = sr_init(&iat, session_begin_params, SR_MIC, &recnotifier);
    if (errcode) {
        printf("speech recognizer init failed\n");
        return;
    }
    errcode = sr_start_listening(&iat);
    if (errcode) {
        printf("start listen failed %d\n", errcode);
       
    }
    /* demo 10 seconds recording */
    while(i++ < 10)
        sleep(1);
    errcode = sr_stop_listening(&iat);
    if (errcode) {
        printf("stop listening failed %d\n", errcode);
    }

    sr_uninit(&iat);
}


/* main thread: start/stop record ; query the result of recgonization.
 * record thread: record callback(data write)
 * helper thread: ui(keystroke detection)
 */

void WakeUp(const std_msgs::String::ConstPtr& msg)
{
    printf("waking up\r\n");
    usleep(700*1000);
    wakeupFlag=1;
}

int main(int argc, char* argv[])
{
    // 初始化ROS
    ros::init(argc, argv, "voiceRecognition");
    ros::NodeHandle n;
    ros::Rate loop_rate(10);

    // 声明Publisher和Subscriber
    // 订阅唤醒语音识别的信号
    ros::Subscriber wakeUpSub = n.subscribe("voiceWakeup", 1000, WakeUp);   
    // 订阅唤醒语音识别的信号    
    pub_voice = n.advertise<sound_play::SoundRequestActionGoal>("/sound_play/goal", 1000);
    ros::Publisher voiceWordsPub = n.advertise<std_msgs::String>("voiceWords", 1000);  
    pub = n.advertise<std_msgs::String>("my_voice", 1000);
    ROS_INFO("Sleeping...");
    int count=0;
    while(ros::ok())
    {
        // 语音识别唤醒
        if (wakeupFlag){
            ROS_INFO("Wakeup...");
            int ret = MSP_SUCCESS;
            const char* login_params = "appid = 58249817, work_dir = .";

            const char* session_begin_params =
                "sub = iat, domain = iat, language = en_us, "
                "accent = mandarin, sample_rate = 16000, "
                "result_type = plain, result_encoding = utf8";

            ret = MSPLogin(NULL, NULL, login_params);
            if(MSP_SUCCESS != ret){
                MSPLogout();
                printf("MSPLogin failed , Error code %d.\n",ret);
            }

            printf("Demo recognizing the speech from microphone\n");
            printf("Speak in 10 seconds\n");
            speak("Start Listening");
            sleep(2);
            demo_mic(session_begin_params);

            printf("10 sec passed\n");
        
            wakeupFlag=0;
            MSPLogout();
        }
        // 语音识别完成
        if(resultFlag){
            resultFlag=0;
            std_msgs::String msg;
            std::string my_str = g_result;
            msg.data = g_result;
            std_msgs::String my_voice;
            my_voice.data=my_str.c_str();
            pub.publish(msg);
            voiceWordsPub.publish(msg);
        }

        ros::spinOnce();
        loop_rate.sleep();
        count++;
    }

exit:
    MSPLogout(); // Logout...

    return 0;
}
