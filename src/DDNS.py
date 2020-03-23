'''
DDNS 主程序 使用阿里云的SDK发起请求
Created By Martin Huang on 2018/5/20
修改记录：
2018/5/20 => 第一版本
2018/5/26 => 增加异常处理、Requst使用单例模式，略有优化
2018/5/29 => 增加网络连通性检测，只有联通时才进行操作，否则等待
2018/6/10 => 使用配置文件存储配置，避免代码内部修改(需要注意Python模块相互引用问题)
2018/9/24 => 修改失败提示信息
'''
from aliyunsdkcore.acs_exception.exceptions import ServerException
from aliyunsdkcore.acs_exception.exceptions import ClientException
from aliyunsdkcore.request import CommonRequest
from Utils import Utils
import time
import argparse
import logging
import os


abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

logger = logging.getLogger("ddns")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d -> %(message)s")

fileHandler = logging.FileHandler("output.log")
fileHandler.setLevel(logging.DEBUG)
fileHandler.setFormatter(formatter)
consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.DEBUG)
consoleHandler.setFormatter(formatter)
logger.addHandler(consoleHandler)
logger.addHandler(fileHandler)


def DDNS(use_v6):
    client = Utils.getAcsClient()
    recordId, lastIp = Utils.getRecordId(Utils.getConfigJson().get('Second-level-domain'))
    if use_v6:
        ip = Utils.getRealIPv6()
        type = 'AAAA'
    else:
        ip = Utils.getRealIP()
        type = 'A'

    logger.info("当前公网IP: %s" % ({'type': type, 'ip': ip}))
    if ip == lastIp:
        logger.info("IP未变更, 不需要修改解析记录, 当前解析IP: %s" % (lastIp))
        return


    request = CommonRequest()
    request.set_domain('alidns.aliyuncs.com')
    request.set_version('2015-01-09')
    request.set_action_name('UpdateDomainRecord')
    request.add_query_param('RecordId', recordId)
    request.add_query_param('RR', Utils.getConfigJson().get('Second-level-domain'))
    request.add_query_param('Type', type)
    request.add_query_param('Value', ip)
    response = client.do_action_with_exception(request)
    logger.info("成功！%s", response)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='DDNS')
    parser.add_argument('-6', '--ipv6', nargs='*', default=False)
    args = parser.parse_args()
    isipv6 = isinstance(args.ipv6, list)

    try:
        while not Utils.isOnline():
            time.sleep(3)
            continue
        DDNS(isipv6)
    except (ServerException,ClientException) as reason:
        logger.error("失败！原因: {0} \n可参考: https://help.aliyun.com/document_detail/29774.html?spm=a2c4g.11186623.2.20.fDjexq#%E9%94%99%E8%AF%AF%E7%A0%81 或阿里云帮助文档".format(reason.get_error_msg()))
