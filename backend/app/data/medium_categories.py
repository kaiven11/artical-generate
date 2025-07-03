# -*- coding: utf-8 -*-
"""
Medium Categories Data
从 https://medium.com/explore-topics 提取的类别和子类别数据
用于前端界面的类别选择功能
"""

MEDIUM_CATEGORIES = {
    "life": {
        "name": "Life",
        "display_name": "生活",
        "tag": "life",
        "subcategories": {
            "family": {
                "name": "Family",
                "display_name": "家庭",
                "tag": "family",
                "children": [
                    {"name": "Adoption", "display_name": "收养", "tag": "adoption"},
                    {"name": "Children", "display_name": "儿童", "tag": "children"},
                    {"name": "Elder Care", "display_name": "老人护理", "tag": "elder-care"},
                    {"name": "Fatherhood", "display_name": "父亲", "tag": "fatherhood"},
                    {"name": "Motherhood", "display_name": "母亲", "tag": "motherhood"},
                    {"name": "Parenting", "display_name": "育儿", "tag": "parenting"},
                    {"name": "Pregnancy", "display_name": "怀孕", "tag": "pregnancy"},
                    {"name": "Seniors", "display_name": "老年人", "tag": "seniors"}
                ]
            },
            "health": {
                "name": "Health",
                "display_name": "健康",
                "tag": "health",
                "children": [
                    {"name": "Aging", "display_name": "衰老", "tag": "aging"},
                    {"name": "Coronavirus", "display_name": "冠状病毒", "tag": "coronavirus"},
                    {"name": "Covid-19", "display_name": "新冠肺炎", "tag": "covid19"},
                    {"name": "Death And Dying", "display_name": "死亡", "tag": "death-and-dying"},
                    {"name": "Disease", "display_name": "疾病", "tag": "disease"},
                    {"name": "Fitness", "display_name": "健身", "tag": "fitness"},
                    {"name": "Mens Health", "display_name": "男性健康", "tag": "mens-health"},
                    {"name": "Nutrition", "display_name": "营养", "tag": "nutrition"},
                    {"name": "Sleep", "display_name": "睡眠", "tag": "sleep"},
                    {"name": "Trans Healthcare", "display_name": "跨性别医疗", "tag": "trans-healthcare"},
                    {"name": "Vaccines", "display_name": "疫苗", "tag": "vaccines"},
                    {"name": "Weight Loss", "display_name": "减肥", "tag": "weight-loss"},
                    {"name": "Womens Health", "display_name": "女性健康", "tag": "womens-health"}
                ]
            },
            "relationships": {
                "name": "Relationships",
                "display_name": "人际关系",
                "tag": "relationships",
                "children": [
                    {"name": "Dating", "display_name": "约会", "tag": "dating"},
                    {"name": "Divorce", "display_name": "离婚", "tag": "divorce"},
                    {"name": "Friendship", "display_name": "友谊", "tag": "friendship"},
                    {"name": "Love", "display_name": "爱情", "tag": "love"},
                    {"name": "Marriage", "display_name": "婚姻", "tag": "marriage"},
                    {"name": "Polyamory", "display_name": "多元恋爱", "tag": "polyamory"}
                ]
            },
            "sexuality": {
                "name": "Sexuality",
                "display_name": "性",
                "tag": "sexuality",
                "children": [
                    {"name": "BDSM", "display_name": "BDSM", "tag": "bdsm"},
                    {"name": "Erotica", "display_name": "情色文学", "tag": "erotica"},
                    {"name": "Kink", "display_name": "性癖", "tag": "kink"},
                    {"name": "Sex", "display_name": "性", "tag": "sex"},
                    {"name": "Sexual Health", "display_name": "性健康", "tag": "sexual-health"}
                ]
            },
            "home": {
                "name": "Home",
                "display_name": "家居",
                "tag": "home",
                "children": [
                    {"name": "Architecture", "display_name": "建筑", "tag": "architecture"},
                    {"name": "Home Improvement", "display_name": "家装", "tag": "home-improvement"},
                    {"name": "Homeownership", "display_name": "房屋所有权", "tag": "homeownership"},
                    {"name": "Interior Design", "display_name": "室内设计", "tag": "interior-design"},
                    {"name": "Rental Property", "display_name": "租赁房产", "tag": "rental-property"},
                    {"name": "Vacation Rental", "display_name": "度假租赁", "tag": "vacation-rental"}
                ]
            },
            "food": {
                "name": "Food",
                "display_name": "美食",
                "tag": "food",
                "children": [
                    {"name": "Baking", "display_name": "烘焙", "tag": "baking"},
                    {"name": "Coffee", "display_name": "咖啡", "tag": "coffee"},
                    {"name": "Cooking", "display_name": "烹饪", "tag": "cooking"},
                    {"name": "Foodies", "display_name": "美食家", "tag": "foodies"},
                    {"name": "Restaurants", "display_name": "餐厅", "tag": "restaurant"},
                    {"name": "Tea", "display_name": "茶", "tag": "tea"}
                ]
            },
            "pets": {
                "name": "Pets",
                "display_name": "宠物",
                "tag": "pets",
                "children": [
                    {"name": "Cats", "display_name": "猫", "tag": "cats"},
                    {"name": "Dog Training", "display_name": "狗训练", "tag": "dog-training"},
                    {"name": "Dogs", "display_name": "狗", "tag": "dogs"},
                    {"name": "Hamsters", "display_name": "仓鼠", "tag": "hamster"},
                    {"name": "Horses", "display_name": "马", "tag": "horses"},
                    {"name": "Pet Care", "display_name": "宠物护理", "tag": "pet-care"}
                ]
            }
        }
    },
    "self-improvement": {
        "name": "Self Improvement",
        "display_name": "自我提升",
        "tag": "self-improvement",
        "subcategories": {
            "mental-health": {
                "name": "Mental Health",
                "display_name": "心理健康",
                "tag": "mental-health",
                "children": [
                    {"name": "Anxiety", "display_name": "焦虑", "tag": "anxiety"},
                    {"name": "Counseling", "display_name": "咨询", "tag": "counseling"},
                    {"name": "Grief", "display_name": "悲伤", "tag": "grief"},
                    {"name": "Life Lessons", "display_name": "人生感悟", "tag": "life-lessons"},
                    {"name": "Self-awareness", "display_name": "自我认知", "tag": "self-awareness"},
                    {"name": "Stress", "display_name": "压力", "tag": "stress"},
                    {"name": "Therapy", "display_name": "治疗", "tag": "therapy"},
                    {"name": "Trauma", "display_name": "创伤", "tag": "trauma"}
                ]
            },
            "productivity": {
                "name": "Productivity",
                "display_name": "生产力",
                "tag": "productivity",
                "children": [
                    {"name": "Career Advice", "display_name": "职业建议", "tag": "career-advice"},
                    {"name": "Coaching", "display_name": "教练", "tag": "coaching"},
                    {"name": "Goal Setting", "display_name": "目标设定", "tag": "goal-setting"},
                    {"name": "Morning Routines", "display_name": "晨间例行", "tag": "morning-routines"},
                    {"name": "Pomodoro Technique", "display_name": "番茄工作法", "tag": "pomodoro-technique"},
                    {"name": "Time Management", "display_name": "时间管理", "tag": "time-management"},
                    {"name": "Work Life Balance", "display_name": "工作生活平衡", "tag": "work-life-balance"}
                ]
            },
            "mindfulness": {
                "name": "Mindfulness",
                "display_name": "正念",
                "tag": "mindfulness",
                "children": [
                    {"name": "Guided Meditation", "display_name": "引导冥想", "tag": "guided-meditation"},
                    {"name": "Journaling", "display_name": "日记", "tag": "journaling"},
                    {"name": "Meditation", "display_name": "冥想", "tag": "meditation"},
                    {"name": "Transcendental Meditation", "display_name": "超觉静坐", "tag": "transcendental-meditation"},
                    {"name": "Yoga", "display_name": "瑜伽", "tag": "yoga"}
                ]
            }
        }
    },
    "work": {
        "name": "Work",
        "display_name": "工作",
        "tag": "work",
        "subcategories": {
            "business": {
                "name": "Business",
                "display_name": "商业",
                "tag": "business",
                "children": [
                    {"name": "Entrepreneurship", "display_name": "创业", "tag": "entrepreneurship"},
                    {"name": "Freelancing", "display_name": "自由职业", "tag": "freelancing"},
                    {"name": "Small Business", "display_name": "小企业", "tag": "small-business"},
                    {"name": "Startups", "display_name": "初创公司", "tag": "startup"},
                    {"name": "Venture Capital", "display_name": "风险投资", "tag": "venture-capital"}
                ]
            },
            "marketing": {
                "name": "Marketing",
                "display_name": "营销",
                "tag": "marketing",
                "children": [
                    {"name": "Advertising", "display_name": "广告", "tag": "advertising"},
                    {"name": "Branding", "display_name": "品牌", "tag": "branding"},
                    {"name": "Content Marketing", "display_name": "内容营销", "tag": "content-marketing"},
                    {"name": "Content Strategy", "display_name": "内容策略", "tag": "content-strategy"},
                    {"name": "Digital Marketing", "display_name": "数字营销", "tag": "digital-marketing"},
                    {"name": "SEO", "display_name": "搜索引擎优化", "tag": "seo"},
                    {"name": "Social Media Marketing", "display_name": "社交媒体营销", "tag": "social-media-marketing"},
                    {"name": "Storytelling For Business", "display_name": "商业故事", "tag": "storytelling-for-business"}
                ]
            },
            "leadership": {
                "name": "Leadership",
                "display_name": "领导力",
                "tag": "leadership",
                "children": [
                    {"name": "Employee Engagement", "display_name": "员工参与", "tag": "employee-engagement"},
                    {"name": "Leadership Coaching", "display_name": "领导力教练", "tag": "leadership-coaching"},
                    {"name": "Leadership Development", "display_name": "领导力发展", "tag": "leadership-development"},
                    {"name": "Management", "display_name": "管理", "tag": "management"},
                    {"name": "Meetings", "display_name": "会议", "tag": "meetings"},
                    {"name": "Org Charts", "display_name": "组织架构", "tag": "org-charts"},
                    {"name": "Thought Leadership", "display_name": "思想领导力", "tag": "thought-leadership"}
                ]
            },
            "remote-work": {
                "name": "Remote Work",
                "display_name": "远程工作",
                "tag": "remote-work",
                "children": [
                    {"name": "Company Retreats", "display_name": "公司团建", "tag": "company-retreats"},
                    {"name": "Digital Nomads", "display_name": "数字游民", "tag": "digital-nomads"},
                    {"name": "Distributed Teams", "display_name": "分布式团队", "tag": "distributed-teams"},
                    {"name": "Future Of Work", "display_name": "工作的未来", "tag": "future-of-work"},
                    {"name": "Work From Home", "display_name": "在家工作", "tag": "work-from-home"}
                ]
            }
        }
    },
    "technology": {
        "name": "Technology",
        "display_name": "技术",
        "tag": "technology",
        "subcategories": {
            "artificial-intelligence": {
                "name": "Artificial Intelligence",
                "display_name": "人工智能",
                "tag": "artificial-intelligence",
                "children": [
                    {"name": "ChatGPT", "display_name": "ChatGPT", "tag": "chatgpt"},
                    {"name": "Conversational AI", "display_name": "对话AI", "tag": "conversational-ai"},
                    {"name": "Deep Learning", "display_name": "深度学习", "tag": "deep-learning"},
                    {"name": "Large Language Models", "display_name": "大语言模型", "tag": "large-language-models"},
                    {"name": "Machine Learning", "display_name": "机器学习", "tag": "machine-learning"},
                    {"name": "NLP", "display_name": "自然语言处理", "tag": "nlp"},
                    {"name": "Voice Assistant", "display_name": "语音助手", "tag": "voice-assistant"}
                ]
            },
            "blockchain": {
                "name": "Blockchain",
                "display_name": "区块链",
                "tag": "blockchain",
                "children": [
                    {"name": "Bitcoin", "display_name": "比特币", "tag": "bitcoin"},
                    {"name": "Cryptocurrency", "display_name": "加密货币", "tag": "cryptocurrency"},
                    {"name": "Decentralized Finance", "display_name": "去中心化金融", "tag": "decentralized-finance"},
                    {"name": "Ethereum", "display_name": "以太坊", "tag": "ethereum"},
                    {"name": "Nft", "display_name": "NFT", "tag": "nft"},
                    {"name": "Web3", "display_name": "Web3", "tag": "web3"}
                ]
            },
            "data-science": {
                "name": "Data Science",
                "display_name": "数据科学",
                "tag": "data-science",
                "children": [
                    {"name": "Analytics", "display_name": "分析", "tag": "analytics"},
                    {"name": "Data Engineering", "display_name": "数据工程", "tag": "data-engineering"},
                    {"name": "Data Visualization", "display_name": "数据可视化", "tag": "data-visualization"},
                    {"name": "Database Design", "display_name": "数据库设计", "tag": "database-design"},
                    {"name": "Sql", "display_name": "SQL", "tag": "sql"}
                ]
            },
            "programming": {
                "name": "Programming",
                "display_name": "编程",
                "tag": "programming",
                "children": [
                    {"name": "Software Development", "display_name": "软件开发", "tag": "software-development"},
                    {"name": "Web Development", "display_name": "Web开发", "tag": "web-development"},
                    {"name": "Mobile Development", "display_name": "移动开发", "tag": "mobile-development"},
                    {"name": "Python", "display_name": "Python", "tag": "python"},
                    {"name": "JavaScript", "display_name": "JavaScript", "tag": "javascript"},
                    {"name": "React", "display_name": "React", "tag": "react"},
                    {"name": "Node.js", "display_name": "Node.js", "tag": "nodejs"}
                ]
            }
        }
    }
}


def get_categories():
    """获取所有类别数据"""
    return MEDIUM_CATEGORIES


def get_category_list():
    """获取扁平化的类别列表，用于前端下拉选择"""
    categories = []

    for main_key, main_category in MEDIUM_CATEGORIES.items():
        # 添加主类别
        categories.append({
            "value": main_category["tag"],
            "label": f"{main_category['display_name']} ({main_category['name']})",
            "type": "main"
        })

        # 添加子类别
        for sub_key, sub_category in main_category["subcategories"].items():
            categories.append({
                "value": sub_category["tag"],
                "label": f"  └ {sub_category['display_name']} ({sub_category['name']})",
                "type": "sub",
                "parent": main_category["tag"]
            })

            # 添加子子类别
            if "children" in sub_category:
                for child in sub_category["children"]:
                    categories.append({
                        "value": child["tag"],
                        "label": f"    └ {child['display_name']} ({child['name']})",
                        "type": "child",
                        "parent": sub_category["tag"],
                        "grandparent": main_category["tag"]
                    })

    return categories


def get_popular_tags():
    """获取热门标签列表"""
    return [
        {"tag": "artificial-intelligence", "display_name": "人工智能", "category": "technology"},
        {"tag": "machine-learning", "display_name": "机器学习", "category": "technology"},
        {"tag": "programming", "display_name": "编程", "category": "technology"},
        {"tag": "data-science", "display_name": "数据科学", "category": "technology"},
        {"tag": "productivity", "display_name": "生产力", "category": "self-improvement"},
        {"tag": "entrepreneurship", "display_name": "创业", "category": "work"},
        {"tag": "leadership", "display_name": "领导力", "category": "work"},
        {"tag": "health", "display_name": "健康", "category": "life"},
        {"tag": "relationships", "display_name": "人际关系", "category": "life"},
        {"tag": "self-improvement", "display_name": "自我提升", "category": "self-improvement"}
    ]


def find_category_by_tag(tag):
    """根据标签查找类别信息"""
    for main_key, main_category in MEDIUM_CATEGORIES.items():
        if main_category["tag"] == tag:
            return main_category

        for sub_key, sub_category in main_category["subcategories"].items():
            if sub_category["tag"] == tag:
                return sub_category

            if "children" in sub_category:
                for child in sub_category["children"]:
                    if child["tag"] == tag:
                        return child

    return None
