# 声明：本代码仅供学习和研究目的使用。使用者应遵守以下原则：
# 1. 不得用于任何商业用途。
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。
# 3. 不得进行大规模爬取或对平台造成运营干扰。
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。
# 5. 不得用于任何非法或不当的用途。
#
# 详细许可条款请参阅项目根目录下的LICENSE文件。
# 使用本代码即表示您同意遵守上述原则和LICENSE中的所有条款。

# 抖音平台配置
PUBLISH_TIME_TYPE = 0

# 指定DY视频ID列表
DY_SPECIFIED_ID_LIST = [
    "7280854932641664319",
    "7202432992642387233",
    # ........................
]

# 指定DY用户ID列表
DY_CREATOR_ID_LIST = [
    "MS4wLjABAAAAjFjaV___jMTYyKhYnm0vytkkqaSyFpRr38T21N57a_wEAVFzIGh8aC8jade1CfN8", #草莓尖尖
    "MS4wLjABAAAARLB42Ur5QHdBwZUetAso8RPYzkJreUJAC5Php4k9yHXejyq6nbRqJEREoGzznsbL", #依依推文
    "MS4wLjABAAAAGshsf2Rmb-PA_kXnLCoza-7PhX4kGvjjNY3Oc76oSQQbLTAK0FEo-tasxSdMd7vT", #甜甜薯
    "MS4wLjABAAAAY4Xm3GLUIbzQG8p59vdd7-dwRywzW-tTnHBhD7HMw8jSZOfCJ-ctCJGbxXgIyh_m", #樱桃花
    "MS4wLjABAAAARLB42Ur5QHdBwZUetAso8RPYzkJreUJAC5Php4k9yHXejyq6nbRqJEREoGzznsbL", #依依推文
    "MS4wLjABAAAArCSDsNIrqkAVnY1WQDZD4U2IbxnCPN6szo_TtiqpV5fo_nq3hp1Vom4_nD3evsGr", #秋刀不吃鱼
    "MS4wLjABAAAAtQDlEkazLfdG6escIuimqWap-F9a4Fr0_a2BtqzevM1hvf33gRIE8-PHIZR-u7Xx", #橙橙子
    "MS4wLjABAAAAFuVXj9KJrq438z6LztpS5LJkVetjVP-A8nVVRNtFVr0KDd3xdmKwi7lzVVj5c3L-", #嘟嘟快长大
    "MS4wLjABAAAAY4Xm3GLUIbzQG8p59vdd7-dwRywzW-tTnHBhD7HMw8jSZOfCJ-ctCJGbxXgIyh_m", #樱桃花🌸
    "MS4wLjABAAAAh5dThTMDZINsg3uli8XQBQ6Gm0jJYeqSV1_uYli3UX1obepBoETi8SpgCLmqtup6", #七七爱听文
    "MS4wLjABAAAAkQW_wfUVflPVgztNYZq6FOWuxdpVjtKfnVfyQUzyQh0", #甜心草莓🍓
    "MS4wLjABAAAAPfMChvyB27fqiwdWIqLNzSIAIepPP2e9TTQIJ9NsJ8A", #美美秋雅
    "MS4wLjABAAAAMdtv44l3Dlt9gtzx5OptsJtMR2q7ili_bVvrWVLslk0", #闪闪同学✨
    "MS4wLjABAAAABxQy7N4kwn7t_TF6m5c5ONB7jrtCT_lU0XzJsroTZHY", #橙子奶糖
    "MS4wLjABAAAAERUfbnpoBhGRNxg6LVj2qSwJO7WU9rvWNNDFwR8Oslk", #心动茉莉
]

# dy排序方式：0:综合排序; 1:最多点赞; 2:最新发布
SEARCH_SORT_TYPE = 2  

# dy发布时间范围：0:不限；1:一天内；7:一周内；180:半年内
PUBLISH_TIME_TYPE = 0  

# 抖音创作者模式下控制爬取数量
# 限制单个创作者爬取的最大视频数量，0表示不限制，如果您想限制100个视频，则设置为100
CRAWLER_MAX_CREATOR_NOTES_COUNT = 30

# 指定只爬取该日期（含）之后的视频。
# 格式为 'YYYY-MM-DD' (例如 '2025-07-25') 或 'today'。留空表示不限制日期。
# 如果设置此项，将优先于CRAWLER_MAX_CREATOR_NOTES_COUNT。
# 程序会检测到非置顶视频发布时间早于该日期时，停止请求新的页面。置顶视频不受此停止条件限制。
DY_CREATOR_CRAWL_TARGET_DATE = "2025-08-07" # 默认不限制日期
