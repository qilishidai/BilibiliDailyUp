"""
core function for scripts
"""

import requests
import random
import json
import time

from utils.data_f import print_f, time_f, random_video_para
from utils.encrypt import get_query
from utils.push import pushplus_push
from utils.cookie_f import formate_cookie, get_csrf
from config import config
from data.api import Api
from data.post_data import PostData
from utils.sever酱 import sever酱推送
from utils.推送到企业微信应用 import 推送消息
from utils.漫画签到 import 检查是否已签到, 漫画签到


class Bilibili:
    """
    Bilibili的等级升级脚本
    你每天可以获得65个经验值
    """

    def __init__(self) -> None:
        self.log = ''
        self.session = requests.Session()
        self.post_data = PostData
        self.api = Api

    def __get_cookie_status(self, ck: str):
        """
            检查cookie是否有效,正常返回0,无效返回1
        """
        cookie = formate_cookie(ck)
        coin_res = self.session.get(url=self.api.coin_url.value,
                                    cookies=cookie).json()
        code = coin_res['code']
        if code != 0:
            # 0有效，-101无效
            return 0
        return 1

    def __get_coin_num(self, ck: str) -> int:
        """
          获取硬币的数量,返回硬币的数量
        """
        cookie = formate_cookie(ck)
        res = self.session.get(
            url=self.api.coin_url.value, headers=self.post_data.headers.value,
            cookies=cookie).json()
        money = res['data']['money']
        if money is None:
            # 当coins num为0时，响应为None
            return 0
        else:
            return money

    def __push_f(self, content: str):
        """
        构建推送数据的字符串
        """
        temp = f'{content}</br>'
        self.log = f'{self.log}{temp}'

    def __inquire_job(self, ck: str) -> tuple:
        """
        检查任务是否已完成

        参数:
            ck (str): 用户的Cookie字符串

        返回值:
            tuple: 包含两个列表的元组，第一个列表是每日任务的完成情况，第二个列表是额外任务的完成情况


        """
        # 格式化Cookie
        cookie = formate_cookie(ck)
        # 发起请求，获取任务完成情况
        inquire_res = self.session.get(
            url=self.api.inquire_url.value, cookies=cookie).json()
        # 提取每日任务的完成情况

        # 打印inquire_res的所有内容
        # print(inquire_res)

        login_job = inquire_res['data']['login']
        watch_job = inquire_res['data']['watch']
        coins_job = inquire_res['data']['coins']
        share_job = inquire_res['data']['share']

        # 提取额外任务的完成情况
        email_job = inquire_res['data']['email']
        tel_job = inquire_res['data']['tel']
        safe_question_job = inquire_res['data']['safe_question']
        identify_card_job = inquire_res['data']['identify_card']

        # 将每日任务和额外任务分别放入列表
        daily_job = [login_job, watch_job, coins_job, share_job]
        extra_job = [email_job, tel_job, safe_question_job, identify_card_job]
        return daily_job, extra_job

    def __get_info(self, ck: str) -> None:
        """
        获取用户信息
        """
        cookie = formate_cookie(ck)
        info_res = self.session.get(url=self.api.info_url.value,
                                    cookies=cookie).json()
        uid = info_res['data']['mid']
        name = info_res['data']['name']
        level = info_res['data']['level']
        current_exp = info_res['data']['level_exp']['current_exp']
        next_exp = info_res['data']['level_exp']['next_exp']
        sub_exp = next_exp - current_exp
        up_days = int(sub_exp / 65)
        coin_num = info_res['data']['coins']
        vip_status = info_res['data']['vip']['status']
        vip_due_data = info_res['data']['vip']['due_date']
        vip_due_data = time_f(vip_due_data)
        if vip_status:
            info_content = f"""用户{name},uid为{uid}您是大会员,大会员到期时间为{vip_due_data},你目前的等级是{level}级,
                        目前的经验{current_exp},离下个等级还差{sub_exp}经验,需要{up_days}天剩余硬币还有{coin_num}个"""

            self.__push_f(f"用户名:{name}</br>uid:{uid}</br>VIP:大会员</br>到期时间:{vip_due_data}"
                          f"</br>目前的等级:{level}级</br>目前的经验:{current_exp}</br>离下个等\
                               级:{sub_exp}经验</br>距升级还差:{up_days}天</br>剩余硬币数:{coin_num}个")

            print_f(info_content)
        else:
            info_content = f"""用户{name},uid为{uid}您的大会员已过期,过期时间为{vip_due_data},你目前的等级是{level}级,
            目前的经验{current_exp},离下个等级还差{sub_exp}经验,需要{up_days}天,剩余硬币还有{coin_num}个"""

            self.__push_f(f"用户名:{name}</br>uid:{uid}</br>VIP:非大会员</br>过期时间:{vip_due_data}</br>目"
                          f"前的等级:{level}级</br>目前的经验:{current_exp}</br>离下个等级:{sub_exp}经验<br>距升级还差:{up_days}天</br>剩余硬币数:{coin_num}个")

            print_f(info_content)

    def __get_video_list(self, ck) -> list:
        """
        投币视频列表
        """
        # uid_list = ['546195', '25876945', '287795639']
        uid_list = config.UID_LIST
        random_uid = random.choice(uid_list)
        headers = self.post_data.video_list_headers.value
        query = get_query(mid=random_uid, ps=30, pn=1)
        headers['path'] = f'/x/space/wbi/arc/search?{query}'
        headers['cookie'] = ck
        get_video_list_url = self.api.get_video_list_url.value.format(query)
        video_res = self.session.get(url=get_video_list_url, headers=headers).json()
        error_count = 0
        while video_res['code']!=0:
            video_res = self.session.get(url=get_video_list_url, headers=headers).json()
            print_f("获取video_list失败,延迟一秒重试")
            time.sleep(1)
            error_count += 1
            if error_count == 10:
                break
        video_list = video_res['data']['list']['vlist']
        return video_list

    def __watch_video(self, bvid: str, ck: str) -> None:
        """
        看视频任务
        """
        watch_time = random.randint(30, 60)
        watch_video_data = self.post_data.watch_video_data.value
        watch_video_data['bvid'] = bvid
        watch_video_data['played_time'] = str(watch_time)
        watch_video_data['csrf'] = get_csrf(ck)
        cookie = formate_cookie(ck)
        watch_video_res = self.session.post(
            url=self.api.watch_video_url.value, data=watch_video_data, cookies=cookie).json()
        code = watch_video_res['code']
        # self.__utools.formate_print(watch_video_res)
        if code == 0:
            print_f('看视频完成')
        else:
            print_f('看视频失败')

    def __share_video(self, bvid: str, ck: str) -> None:
        """
        分享视频任务
        """
        share_video_data = self.post_data.share_video_data.value
        share_video_data['bvid'] = bvid
        share_video_data['csrf'] = get_csrf(ck)
        cookie = formate_cookie(ck)
        share_video_res = self.session.post(
            url=self.api.share_video_url.value, data=share_video_data, cookies=cookie,
            headers=self.post_data.headers.value).json()
        code = share_video_res['code']

        if code == 0:
            print_f('分享视频成功')
        else:
            print_f('分享视频失败')

    def __insert_coin(self, aid: str, ck: str) -> int:
        """
        insert coins function
        """
        cookie = formate_cookie(ck)
        insert_coin_data = self.post_data.insert_coin_data.value
        insert_coin_headers = self.post_data.insert_coin_headers.value
        insert_coin_data['aid'] = aid
        insert_coin_data['csrf'] = get_csrf(ck)
        insert_coin_headers['cookie'] = ck
        insert_coin_res = self.session.post(
            url=self.api.insert_coins_url.value, headers=insert_coin_headers,
            data=insert_coin_data, cookies=cookie).json()
        like = insert_coin_res['data']['like']
        if like:
            print_f('投币成功')
            return 1
        else:
            print_f('投币失败')
            return 0

    def __do_insert_coins(self, ck: str) -> int:
        """
        insert coin function
        """
        video_list = self.__get_video_list(ck)
        bvid, title, author, aid = random_video_para(video_list)
        print_f(f'开始向{author}的视频{title}投币……')
        coin_res = self.__insert_coin(aid, ck)
        return coin_res

    def __do_live_sign(self, ck: str) -> None:
        """
        直播任务
        """

        res = self.session.get(url=self.api.live_sign_url.value,
                               cookies=formate_cookie(ck)).json()
        if res['code'] == 0:
            text = res['data']['text']
            sign_days = res['data']['hadSignDays']
            self.__push_f('直播签到:签到成功,签到天数为{}'.format(sign_days))
            print_f(f'签到奖励:{text},连续签到{sign_days}天')
            self.__push_f(f'签到奖励:{text},连续签到{sign_days}天')
        else:
            print_f('直播签到:当天已签到~')
            self.__push_f('直播签到:当天已签到')

    def __inquire_live_info(self, ck: str) -> bool:
        """
        返回银瓜子数量
        """
        res = self.session.get(url=self.api.live_info_url.value,
                               cookies=formate_cookie(ck)).json()
        self.__push_f(f'银瓜子数量:{res["data"]["silver"]}')
        print_f(f'银瓜子数量:{res["data"]["silver"]}')
        if res['data']['silver'] > 700:
            return True
        return False

    def __do_silver2coin(self, ck: str) -> None:
        """银瓜子换硬币"""
        silver_data = self.post_data.silver2coin_data.value
        csrf_value = get_csrf(ck)
        silver_data['csrf'] = csrf_value
        silver_data['csrf_token'] = csrf_value
        res = self.session.post(url=self.api.silver2coin_url.value,
                                cookies=formate_cookie(ck), data=silver_data).json()
        if res['code'] == 0:
            silver = res['data']['silver']
            print_f('银瓜子兑换:成功!')
            print_f(f'银瓜子剩余:{silver}个')
            self.__push_f('银瓜子兑换:成功!')
            self.__push_f(f'银瓜子剩余:{silver}个')
        else:
            print_f('银瓜子兑换:当天已兑换!')
            self.__push_f('银瓜子兑换:当天已兑换!')

    def watch_video_task(self, ck):
        print_f('观看视频任务未完成,即将开始观看视频任务……')
        video_list = self.__get_video_list(ck)
        bvid, title, author, aid = random_video_para(video_list)
        print_f(f'开始观看作者{author}的视频{title}……')
        self.__watch_video(bvid, ck)
        print_f('观看视频任务已完成，即将开始下一个任务……')
        self.__push_f('观看视频:完成~获得5点经验值')

    def insert_coin_task(self, ck, coin_num, coin_has_inserted_num):
        if config.COIN_OR_NOT and coin_num >= 5:
            print_f('投币任务未完成,即将开始投币任务')
            if config.COIN_NUM == -1:
                coin_count = int((50 - coin_has_inserted_num) / 10)
            else:
                coin_count = config.COIN_NUM
            print_f(f'本次投币任务数量:{coin_count}')
            success_count = 0
            fail_count = 0
            for x in range(0, coin_count):
                job_count = 0
                if config.STRICT_MODE:
                    while 1:
                        coin_res = self.__do_insert_coins(ck)
                        job_count += 1
                        if coin_res or job_count == 5:
                            success_count += 1
                            # Prevent the dead cycle of coins all the time
                            break
                        else:
                            fail_count += 1
                        time.sleep(2)
                    print_f(f'当前投币成功{success_count},失败{fail_count}次')
                else:
                    self.__do_insert_coins(ck)
                    time.sleep(2)
                time.sleep(1)
            print_f('投币任务已完成，即将开始下一个任务……')
            self.__push_f(f'每日投币:完成~获得{coin_count * 10}点经验值')
            return coin_num

    def share_video_task(self,ck):
        video_list = self.__get_video_list(ck)
        bvid, title, author, aid = random_video_para(video_list)
        print_f(f'开始分享{author}的视频{title}……')
        self.__share_video(bvid, ck)

    def __do_job(self, ck: str) -> None:
        """
        开始执行任务,执行所有任务的函数
        """
        cookie_status = self.__get_cookie_status(ck)
        if cookie_status:
            coin_num = self.__get_coin_num(ck)
            print_f('cookie有效即将开始查询任务……')
            print_f('=========以下是任务信息=========')
            self.__push_f('=========以下是任务信息=========')
            # self.__get_info()
            inquire_job_res = self.__inquire_job(ck)
            daily_job, extra_job = inquire_job_res

            for index, job in enumerate(daily_job):
                if index == 0:
                    print_f('登录任务已完成') if job else print_f('登录任务未完成')
                    self.__push_f('每日登录:已完成~获得5点经验值')
                elif index == 1:
                    if job:
                        print_f('观看视频任务已完成')
                        self.__push_f('观看视频:已完成~获得5点经验值')
                    else:
                        self.watch_video_task(ck)
                elif index == 2:
                    if config.COIN_OR_NOT and coin_num >= 5:
                        if job == 50:
                            print_f('投币任务已完成')
                            self.__push_f('每日投币:已完成~获得50点经验值')
                        else:
                            print_f('投币任务未完成,即将开始投币任务')
                            coin_count = self.insert_coin_task(ck, coin_num, job)
                            print_f('投币任务已完成，即将开始下一个任务……')
                            self.__push_f(f'每日投币:完成~获得{coin_count * 10}点经验值')
                    else:
                        print_f('投币任务已跳过')
                        self.__push_f('每日投币:跳过~')
                else:
                    if job:
                        print_f('分享任务已完成')
                        self.__push_f('每日分享:已完成~获得5点经验值')
                    else:
                        print_f('分享任务未完成,即将开始分享任务……')
                        self.share_video_task(ck)
                        print_f('分享任务已完成,日常任务已全部完成!即将查询额外任务……')
                        self.__push_f('每日分享:完成~获得5点经验值')
                        time.sleep(1)

            print_f('==========以下是额外任务==============')
            self.__push_f('=========以下是额外任务=========')

            for index, job in enumerate(extra_job):
                if index == 0:
                    if job:
                        print_f('绑定邮箱任务已完成')
                        self.__push_f('绑定邮箱:已完成')
                    else:
                        print_f('绑定邮箱任务未完成,完成可以获得20点经验值~')
                        self.__push_f('绑定邮箱:未完成~完成可获得20点经验')
                elif index == 1:
                    if job:
                        print_f('绑定手机任务已完成')
                        self.__push_f('绑定手机:已完成')
                    else:
                        print_f('绑定手机任务未完成,完成可以获得100点经验值~')
                        self.__push_f('绑定手机:未完成~完成可获得20点经验')
                elif index == 2:
                    if job:
                        print_f('设置密保任务已完成')
                        self.__push_f('密保任务:已完成')
                    else:
                        print_f('设置密保任务未完成,完成可以获得30点经验值~')
                        self.__push_f('密保任务:未完成~完成可获得30点经验')
                else:
                    if job:
                        print_f('实名认证任务已完成')
                        self.__push_f('实名认证:已完成')
                    else:
                        print_f('实名认证任务未完成,完成可以获得50点经验值~')
                        self.__push_f('实名认证:未完成~完成可获得50点经验')
            print_f('==========以下是直播任务==============')
            self.__push_f('=========以下是直播任务=========')
            self.__do_live_sign(ck)
            if config.SILVER2COIN_OR_NOT and self.__inquire_live_info(ck):
                # 银瓜子小于700也会跳过任务
                self.__do_silver2coin(ck)
            else:
                self.__push_f('银瓜子转换币:跳过~')
                print_f('银瓜子兑换:跳过~')

            self.__push_f('=========漫画签到情况========')
            print_f('=========漫画签到情况=========')
            if not 检查是否已签到(ck):
                if 漫画签到(ck):
                    print_f("漫画签到:已完成~")
                    self.__push_f("漫画签到:已完成~")
                else:
                    print_f("漫画签到失败")
                    self.__push_f("漫画签到失败")
            else:
                print_f("漫画签到:当天已签到~")
                self.__push_f("漫画签到:当天已签到~")

            self.__push_f('=========以下是个人信息=========')
            print_f('=========以下是个人信息=========')
            self.__get_info(ck)

        else:
            print_f('cookie已失效,任务停止,请更换新的cookie!')
            self.__push_f('cookie已失效,任务停止,请更换新的cookie!')
        print_f('==========分割线==============')

    def go(self) -> None:
        """
        Entrance function
        """
        print_f(f'成功添加{len(config.COOKIE_LIST)}个cookie,开始任务……')
        for index, ck in enumerate(config.COOKIE_LIST):
            self.__push_f(f'=========这是第{index + 1}个账号=========')
            print_f(f'正在签到第{index + 1}个账号……')
            self.__do_job(ck)
            time.sleep(1)
        if config.PUSH_OR_NOT:
            pushplus_push(config.TOKEN, self.log)
        if config.企业ID != "" and config.企业应用secret != "" and config.企业应用的id != "":
            #下面第一个参数,使用字符串的 replace() 方法来替换字符串中的 </br> 为换行符 \n。
            推送消息(self.log.replace("</br>", "\n"),config.企业ID, config.企业应用secret, config.企业应用的id)
        if config.推送到sever酱key!="":
            sever酱推送(self.log.replace("</br>", "\n"),config.推送到sever酱key)