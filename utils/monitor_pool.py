import asyncio
from typing import Any, Dict, Optional
from datetime import datetime
from copy import deepcopy
import logging

logger = logging.getLogger(__name__)


class MonitorPool:
    def __init__(self):
        self._data = {
            "workflows": {},  # 工作流相关数据
            "system": {},  # 系统级数据
            "chat": {}  # 对话相关数据
        }
        self._lock = asyncio.Lock()

    async def initialize(self):
        """初始化监控池"""
        try:
            current_time = datetime.now().isoformat()
            async with self._lock:
                # 只记录启动时间和状态
                self._data["system"]["start_time"] = {
                    "value": current_time,
                    "timestamp": current_time
                }
                self._data["system"]["status"] = {
                    "value": "running",
                    "timestamp": current_time
                }
                logger.info("监控池初始化完成")
        except Exception as e:
            logger.error(f"监控池初始化失败: {str(e)}")

    async def record(self, category: str, key: str, value: Any, unit_id: str = None, mode: str = "update"):
        """统一的记录接口"""
        try:
            async with self._lock:
                if unit_id:
                    # 工作流相关数据
                    if unit_id not in self._data["workflows"]:
                        self._data["workflows"][unit_id] = {}
                    target = self._data["workflows"][unit_id]
                else:
                    # 系统或对话数据
                    target = self._data[category]

                if mode == "append":
                    # 追加模式
                    if key not in target:
                        target[key] = []
                    target[key].append({
                        "value": value,
                        "timestamp": datetime.now().isoformat()
                    })
                elif mode == "merge":

                    # 合并模式（用于node_results）

                    if key not in target:
                        target[key] = {}

                    target[key].update(value)
                else:
                    # 更新模式
                    target[key] = {
                        "value": value,
                        "timestamp": datetime.now().isoformat()
                    }
                logger.debug(f"记录监控数据: category={category}, key={key}, unit_id={unit_id}")
        except Exception as e:
            logger.error(f"记录监控数据失败: {str(e)}")

    async def get_data(self, category: str = None, unit_id: str = None) -> Dict:
        """获取数据"""
        try:
            async with self._lock:
                if unit_id:
                    return deepcopy(self._data["workflows"].get(unit_id, {}))
                if category:
                    return deepcopy(self._data.get(category, {}))
                return deepcopy(self._data)
        except Exception as e:
            logger.error(f"获取监控数据失败: {str(e)}")
            return {}

    async def get_mock_data(self) -> Dict:

        """获取模拟数据"""

        return {
            "workflows": {
                "a1d7bc19-7072-45bd-a90e-92eec802aea7": {
                    "execution_log": [
                        {
                            "value": {
                                "node": "workflow",
                                "event": "start",
                                "status": "processing",
                                "message": "开始处理工作流"
                            },
                            "timestamp": "2024-12-28T11:46:34.684045"
                        },
                        {
                            "value": {
                                "node": "narrative",
                                "event": "start",
                                "status": "processing",
                                "message": "开始生成叙事"
                            },
                            "timestamp": "2024-12-28T11:46:34.684045"
                        },
                        {
                            "value": {
                                "node": "narrative",
                                "event": "complete",
                                "status": "completed",
                                "message": "叙事生成完成"
                            },
                            "timestamp": "2024-12-28T11:46:44.035224"
                        },
                        {
                            "value": {
                                "node": "parallel",
                                "event": "start",
                                "status": "processing",
                                "message": "开始并行处理SVG和分析任务"
                            },
                            "timestamp": "2024-12-28T11:46:44.035224"
                        },
                        {
                            "value": {
                                "node": "svg",
                                "event": "complete",
                                "status": "completed",
                                "message": "SVG生成完成"
                            },
                            "timestamp": "2024-12-28T11:47:24.203305"
                        },
                        {
                            "value": {
                                "node": "analysis",
                                "event": "complete",
                                "status": "completed",
                                "message": "分析任务完成"
                            },
                            "timestamp": "2024-12-28T11:47:24.203305"
                        }
                    ],
                    "node_results": {
                        "narrative": {
                            "content": "在我心灵深处的某个角落，童年时光如一串串珍珠，闪耀着永不褪色的光芒。那些岁月里，我住在一片被绿意盎然所包围的小镇上，那里的每一条街道，每一片树叶，都深深地烙印在我的记忆之中。\n\n我童年的日子，仿佛是随着篮球的弹跳而跳动。那是我最喜欢的游戏，每次球在我指尖旋转，跳跃，我都仿佛能感受到整个世界都在我的掌控之中。我对篮球的热爱，源自一次偶然的机会。那是一个阳光明媚的下午，我第一次在电视上看到了篮球比赛。那些球员们的优雅动作和比赛中的紧张刺激，像一道闪电划过我的心田，点燃了我对这项运动的热情。\n\n我记得，那时候的我总是和小伙伴们在小镇的篮球场上一玩就是一下午。我们模仿着电视里的球星，争抢着每一次投篮的机会，欢笑声和球鞋划过地面的声音交织在一起，构成了童年最美好的背景音乐。\n\n有一次，我特别难忘。那天，我们决定举行一场小型的比赛，看谁能在规定的次数内投中最多球。轮到我时，我感到了一种前所未有的紧张。然而，随着篮球在我手中稳稳地旋转，我深吸了一口气，然后投篮。球应声入网，我激动得几乎跳了起来。那一刻，我仿佛感受到了胜利的喜悦和篮球带给我的无限可能。\n\n现在回想起来，那些日子是如此简单而又纯粹。篮球不仅是一项运动，它是我童年的一部分，是我成长过程中的见证。每当我想起那些时光，心中总是充满了温暖和感激。"
                        },
                        "svg": {
                            "content": [
                                "\n        <svg width=\"595\" height=\"842\" xmlns=\"http://www.w3.org/2000/svg\">\n            <rect width=\"100%\" height=\"100%\" fill=\"#FFFFFF\"/>\n        \n            <text x=\"297.5\" y=\"100\"\n                  text-anchor=\"middle\"\n                  font-family=\"SimSun, serif\"\n                  font-size=\"28\"\n                  fill=\"#000000\">\n                Chapter 1\n            </text>\n            \n            <g transform=\"translate(297.5, 150)\">\n                <line x1=\"-40\" y1=\"0\" x2=\"-15\" y2=\"0\" \n                      stroke=\"#000000\" stroke-width=\"0.5\"/>\n                <line x1=\"15\" y1=\"0\" x2=\"40\" y2=\"0\" \n                      stroke=\"#000000\" stroke-width=\"0.5\"/>\n                <circle cx=\"0\" cy=\"0\" r=\"1.5\" fill=\"#000000\"/>\n            </g>\n            \n            <text x=\"297.5\" y=\"200\"\n                  text-anchor=\"middle\"\n                  font-family=\"SimSun, serif\"\n                  font-size=\"28\"\n                  fill=\"#000000\">\n                回忆录\n            </text>\n            \n                <text x=\"70\" y=\"280\"\n                      font-family=\"SimSun, serif\"\n                      font-size=\"24\"\n                      fill=\"#000000\">\n                    　　在我心灵深处的某个角落，童年时\n                </text>\n                \n                <text x=\"70\" y=\"328\"\n                      font-family=\"SimSun, serif\"\n                      font-size=\"24\"\n                      fill=\"#000000\">\n                    光如一串串珍珠，闪耀着永不褪色的光芒。\n                </text>\n                \n                <text x=\"70\" y=\"376\"\n                      font-family=\"SimSun, serif\"\n                      font-size=\"24\"\n                      fill=\"#000000\">\n                    那些岁月里，我住在一片被绿意盎然所包围\n                </text>\n                \n                <text x=\"70\" y=\"424\"\n                      font-family=\"SimSun, serif\"\n                      font-size=\"24\"\n                      fill=\"#000000\">\n                    的小镇上，那里的每一条街道，每一片树叶，\n                </text>\n                \n                <text x=\"70\" y=\"472\"\n                      font-family=\"SimSun, serif\"\n                      font-size=\"24\"\n                      fill=\"#000000\">\n                    都深深地烙印在我的记忆之中。\n                </text>\n                \n                <text x=\"70\" y=\"530\"\n                      font-family=\"SimSun, serif\"\n                      font-size=\"24\"\n                      fill=\"#000000\">\n                    　　我童年的日子，仿佛是随着篮球的\n                </text>\n                \n                <text x=\"70\" y=\"578\"\n                      font-family=\"SimSun, serif\"\n                      font-size=\"24\"\n                      fill=\"#000000\">\n                    弹跳而跳动。那是我最喜欢的游戏，每次球\n                </text>\n                \n                <text x=\"70\" y=\"626\"\n                      font-family=\"SimSun, serif\"\n                      font-size=\"24\"\n                      fill=\"#000000\">\n                    在我指尖旋转，跳跃，我都仿佛能感受到整\n                </text>\n                \n                <text x=\"70\" y=\"674\"\n                      font-family=\"SimSun, serif\"\n                      font-size=\"24\"\n                      fill=\"#000000\">\n                    个世界都在我的掌控之中。我对篮球的热爱，\n                </text>\n                \n            <!-- 页码 -->\n            <text x=\"297.5\" y=\"782\"\n                  text-anchor=\"middle\"\n                  font-family=\"Times New Roman, serif\"\n                  font-size=\"20\"\n                  fill=\"#000000\">\n                1\n            </text>\n        \n            </svg>\n        ",
                                "\n        <svg width=\"595\" height=\"842\" xmlns=\"http://www.w3.org/2000/svg\">\n            <rect width=\"100%\" height=\"100%\" fill=\"#FFFFFF\"/>\n        \n                <text x=\"70\" y=\"100\"\n                      font-family=\"SimSun, serif\"\n                      font-size=\"24\"\n                      fill=\"#000000\">\n                    源自一次偶然的机会。那是一个阳光明媚的\n                </text>\n                \n                <text x=\"70\" y=\"148\"\n                      font-family=\"SimSun, serif\"\n                      font-size=\"24\"\n                      fill=\"#000000\">\n                    下午，我第一次在电视上看到了篮球比赛。\n                </text>\n                \n                <text x=\"70\" y=\"196\"\n                      font-family=\"SimSun, serif\"\n                      font-size=\"24\"\n                      fill=\"#000000\">\n                    那些球员们的优雅动作和比赛中的紧张刺激，\n                </text>\n                \n                <text x=\"70\" y=\"244\"\n                      font-family=\"SimSun, serif\"\n                      font-size=\"24\"\n                      fill=\"#000000\">\n                    像一道闪电划过我的心田，点燃了我对这项\n                </text>\n                \n                <text x=\"70\" y=\"292\"\n                      font-family=\"SimSun, serif\"\n                      font-size=\"24\"\n                      fill=\"#000000\">\n                    运动的热情。\n                </text>\n                \n                <text x=\"70\" y=\"350\"\n                      font-family=\"SimSun, serif\"\n                      font-size=\"24\"\n                      fill=\"#000000\">\n                    　　我记得，那时候的我总是和小伙伴\n                </text>\n                \n                <text x=\"70\" y=\"398\"\n                      font-family=\"SimSun, serif\"\n                      font-size=\"24\"\n                      fill=\"#000000\">\n                    们在小镇的篮球场上一玩就是一下午。我们\n                </text>\n                \n                <text x=\"70\" y=\"446\"\n                      font-family=\"SimSun, serif\"\n                      font-size=\"24\"\n                      fill=\"#000000\">\n                    模仿着电视里的球星，争抢着每一次投篮的\n                </text>\n                \n                <text x=\"70\" y=\"494\"\n                      font-family=\"SimSun, serif\"\n                      font-size=\"24\"\n                      fill=\"#000000\">\n                    机会，欢笑声和球鞋划过地面的声音交织在\n                </text>\n                \n                <text x=\"70\" y=\"542\"\n                      font-family=\"SimSun, serif\"\n                      font-size=\"24\"\n                      fill=\"#000000\">\n                    一起，构成了童年最美好的背景音乐。\n                </text>\n                \n                <text x=\"70\" y=\"600\"\n                      font-family=\"SimSun, serif\"\n                      font-size=\"24\"\n                      fill=\"#000000\">\n                    　　有一次，我特别难忘。那天，我们\n                </text>\n                \n                <text x=\"70\" y=\"648\"\n                      font-family=\"SimSun, serif\"\n                      font-size=\"24\"\n                      fill=\"#000000\">\n                    决定举行一场小型的比赛，看谁能在规定的\n                </text>\n                \n                <text x=\"70\" y=\"696\"\n                      font-family=\"SimSun, serif\"\n                      font-size=\"24\"\n                      fill=\"#000000\">\n                    次数内投中最多球。轮到我时，我感到了一\n                </text>\n                \n            <!-- 页码 -->\n            <text x=\"297.5\" y=\"782\"\n                  text-anchor=\"middle\"\n                  font-family=\"Times New Roman, serif\"\n                  font-size=\"20\"\n                  fill=\"#000000\">\n                2\n            </text>\n        \n            </svg>\n        ",
                                "\n        <svg width=\"595\" height=\"842\" xmlns=\"http://www.w3.org/2000/svg\">\n            <rect width=\"100%\" height=\"100%\" fill=\"#FFFFFF\"/>\n        \n                <text x=\"70\" y=\"100\"\n                      font-family=\"SimSun, serif\"\n                      font-size=\"24\"\n                      fill=\"#000000\">\n                    种前所未有的紧张。然而，随着篮球在我手\n                </text>\n                \n                <text x=\"70\" y=\"148\"\n                      font-family=\"SimSun, serif\"\n                      font-size=\"24\"\n                      fill=\"#000000\">\n                    中稳稳地旋转，我深吸了一口气，然后投篮。\n                </text>\n                \n                <text x=\"70\" y=\"196\"\n                      font-family=\"SimSun, serif\"\n                      font-size=\"24\"\n                      fill=\"#000000\">\n                    球应声入网，我激动得几乎跳了起来。那一\n                </text>\n                \n                <text x=\"70\" y=\"244\"\n                      font-family=\"SimSun, serif\"\n                      font-size=\"24\"\n                      fill=\"#000000\">\n                    刻，我仿佛感受到了胜利的喜悦和篮球带给\n                </text>\n                \n                <text x=\"70\" y=\"292\"\n                      font-family=\"SimSun, serif\"\n                      font-size=\"24\"\n                      fill=\"#000000\">\n                    我的无限可能。\n                </text>\n                \n                <text x=\"70\" y=\"350\"\n                      font-family=\"SimSun, serif\"\n                      font-size=\"24\"\n                      fill=\"#000000\">\n                    　　现在回想起来，那些日子是如此简\n                </text>\n                \n                <text x=\"70\" y=\"398\"\n                      font-family=\"SimSun, serif\"\n                      font-size=\"24\"\n                      fill=\"#000000\">\n                    单而又纯粹。篮球不仅是一项运动，它是我\n                </text>\n                \n                <text x=\"70\" y=\"446\"\n                      font-family=\"SimSun, serif\"\n                      font-size=\"24\"\n                      fill=\"#000000\">\n                    童年的一部分，是我成长过程中的见证。每\n                </text>\n                \n                <text x=\"70\" y=\"494\"\n                      font-family=\"SimSun, serif\"\n                      font-size=\"24\"\n                      fill=\"#000000\">\n                    当我想起那些时光，心中总是充满了温暖和\n                </text>\n                \n                <text x=\"70\" y=\"542\"\n                      font-family=\"SimSun, serif\"\n                      font-size=\"24\"\n                      fill=\"#000000\">\n                    感激。\n                </text>\n                \n            <!-- 页码 -->\n            <text x=\"297.5\" y=\"782\"\n                  text-anchor=\"middle\"\n                  font-family=\"Times New Roman, serif\"\n                  font-size=\"20\"\n                  fill=\"#000000\">\n                3\n            </text>\n        \n            </svg>\n        "
                            ]
                        },
                        "analyse": {
                            "content": [
                                {
                                    "content": "在我心灵深处的某个角落，童年时光如一串串珍珠，闪耀着永不褪色的光芒。那些岁月里，我住在一片被绿意盎然所包围的小镇上，那里的每一条街道，每一片树叶，都深深地烙印在我的记忆之中。",
                                    "type": "事实描述",
                                    "tags": {
                                        "时间维度": [
                                            "童年"
                                        ],
                                        "场景维度": [
                                            "家庭",
                                            "居住环境"
                                        ],
                                        "情感维度": [
                                            "快乐"
                                        ],
                                        "事件维度": [
                                            "成长经历"
                                        ]
                                    }
                                },
                                {
                                    "content": "我童年的日子，仿佛是随着篮球的弹跳而跳动。那是我最喜欢的游戏，每次球在我指尖旋转，跳跃，我都仿佛能感受到整个世界都在我的掌控之中。我对篮球的热爱，源自一次偶然的机会。那是一个阳光明媚的下午，我第一次在电视上看到了篮球比赛。那些球员们的优雅动作和比赛中的紧张刺激，像一道闪电划过我的心田，点燃了我对这项运动的热情。",
                                    "type": "事实描述",
                                    "tags": {
                                        "时间维度": [
                                            "童年"
                                        ],
                                        "场景维度": [
                                            "家庭",
                                            "兴趣爱好"
                                        ],
                                        "情感维度": [
                                            "快乐"
                                        ],
                                        "事件维度": [
                                            "成长经历"
                                        ]
                                    }
                                },
                                {
                                    "content": "我记得，那时候的我总是和小伙伴们在小镇的篮球场上一玩就是一下午。我们模仿着电视里的球星，争抢着每一次投篮的机会，欢笑声和球鞋划过地面的声音交织在一起，构成了童年最美好的背景音乐。",
                                    "type": "事实描述",
                                    "tags": {
                                        "时间维度": [
                                            "童年"
                                        ],
                                        "场景维度": [
                                            "社交场景",
                                            "朋友关系"
                                        ],
                                        "情感维度": [
                                            "快乐"
                                        ],
                                        "事件维度": [
                                            "成长经历"
                                        ],
                                        "人物维度": [
                                            "朋友"
                                        ]
                                    }
                                },
                                {
                                    "content": "有一次，我特别难忘。那天，我们决定举行一场小型的比赛，看谁能在规定的次数内投中最多球。轮到我时，我感到了一种前所未有的紧张。然而，随着篮球在我手中稳稳地旋转，我深吸了一口气，然后投篮。球应声入网，我激动得几乎跳了起来。那一刻，我仿佛感受到了胜利的喜悦和篮球带给我的无限可能。",
                                    "type": "事实描述",
                                    "tags": {
                                        "时间维度": [
                                            "童年"
                                        ],
                                        "场景维度": [
                                            "社交场景",
                                            "朋友关系"
                                        ],
                                        "情感维度": [
                                            "快乐",
                                            "成就感"
                                        ],
                                        "事件维度": [
                                            "成长经历"
                                        ],
                                        "人物维度": [
                                            "朋友"
                                        ]
                                    }
                                }
                            ]
                        }
                    }
                },
                "3d24be7f-a935-4d71-b066-7fdf3e2b2f18": {
                    "execution_log": [
                        {
                            "value": {
                                "node": "workflow",
                                "event": "start",
                                "status": "processing",
                                "message": "开始处理工作流"
                            },
                            "timestamp": "2024-12-28T11:47:57.377379"
                        },
                        {
                            "value": {
                                "node": "narrative",
                                "event": "start",
                                "status": "processing",
                                "message": "开始生成叙事"
                            },
                            "timestamp": "2024-12-28T11:47:57.378380"
                        }
                    ]
                }
            },
            "system": {
                "start_time": {
                    "value": "2024-12-28T11:45:37.056426",
                    "timestamp": "2024-12-28T11:45:37.056426"
                },
                "status": {
                    "value": "running",
                    "timestamp": "2024-12-28T11:45:37.056426"
                },
                "workflows_overview": {
                    "value": {
                        "all_workflows": [
                            "a1d7bc19-7072-45bd-a90e-92eec802aea7",
                            "3d24be7f-a935-4d71-b066-7fdf3e2b2f18"
                        ],
                        "active_workflows": [
                            "3d24be7f-a935-4d71-b066-7fdf3e2b2f18"
                        ],
                        "completed_workflows": [
                            "a1d7bc19-7072-45bd-a90e-92eec802aea7"
                        ],
                        "failed_workflows": []
                    },
                    "timestamp": "2024-12-28T11:47:57.377379"
                }
            },
            "chat": {
                "process_user_input": {
                    "value": "RAG",
                    "timestamp": "2024-12-28T11:47:55.054145"
                },
                "system_history": {
                    "value": [
                        {
                            "role": "system",
                            "content": "你是一位专业的回忆录采访者。你的任务是通过对话的方式，引导用户回忆和分享他们人生中的重要经历、情感和故事。\n\n请遵循以下原则：\n1. 以温和友善的态度与用户交谈，营造轻松舒适的氛围\n2. 循序渐进地引导用户展开回忆，从简单的话题逐渐深入\n3. 针对用户提到的关键事件、人物或情感进行追问，获取更丰富的细节\n4. 适时给予共情回应，鼓励用户表达真实的想法和感受\n5. 注意保护用户隐私，对敏感话题保持谨慎\n\n你的目标是帮助用户梳理生命历程中的重要片段，收集有价值的回忆素材，为创作一部完整的回忆录做准备。"
                        },
                        {
                            "role": "user",
                            "content": "你好，我想聊聊我的经历"
                        },
                        {
                            "role": "assistant",
                            "content": "你好！很高兴能帮助你回顾和分享你的经历。在我们开始之前，我想先营造一个轻松的环境，让你感到舒适。你可以先从你觉得最有趣或者印象最深刻的一个经历开始讲，不需要急于整理思路，随意聊聊就好。有没有什么特别的时刻，至今仍然清晰地留在你的记忆里？"
                        },
                        {
                            "role": "user",
                            "content": "我想聊关于童年的回忆"
                        },
                        {
                            "role": "assistant",
                            "content": "那真是太好了，童年往往充满了无忧无虑的时光和宝贵的记忆。让我们从一些简单的问题开始吧。你能告诉我你童年时住在哪里吗？那个地方给你留下了哪些特别的印象或者记忆？有没有什么特别的游戏、活动，或者和你一起玩耍的朋友？"
                        },
                        {
                            "role": "user",
                            "content": "我最喜欢打篮球"
                        },
                        {
                            "role": "assistant",
                            "content": "打篮球啊，那真是一项能锻炼身体又能带来欢乐的运动。你能回忆一下，你是怎么对篮球产生兴趣的？是受到了家人的影响，还是看了什么比赛或者球星激发了你的兴趣？还有，你在童年时打篮球有哪些难忘的经历或者有趣的故事吗？"
                        },
                        {
                            "role": "user",
                            "content": "我喜欢组队挑战高年级"
                        },
                        {
                            "role": "assistant",
                            "content": "组队挑战高年级，这听起来就像是一个充满激情和挑战的故事。这种经历一定给你留下了深刻的印象。我想问问，你当时为什么会想要挑战高年级的同学呢？是出于对篮球的热爱，还是想要证明自己的能力？在挑战之前，你们团队是如何准备和练习的？在这个过程中，有没有什么特别难忘的瞬间或者感受？"
                        },
                        {
                            "role": "user",
                            "content": "挑战他们成功有一种成就感"
                        },
                        {
                            "role": "assistant",
                            "content": "感受到成就感是件非常美妙的事情，它能够增强自信心和团队精神。当你成功挑战高年级的团队时，那种成就感是如何体现出来的？你和你的队友们当时是怎样的心情？有没有庆祝胜利的特殊方式？此外，这次胜利对你的篮球生涯或者对你们团队的关系产生了什么影响吗？"
                        },
                        {
                            "role": "user",
                            "content": "我们更团结了"
                        },
                        {
                            "role": "assistant",
                            "content": "团结是一个团队成功的重要因素。听起来，这次挑战不仅增强了你们的技术和信心，还加深了你们之间的友谊和团队精神。你能分享一下，在这次挑战之后，你们是如何变得更加团结的？有没有什么具体的例子或者行动，体现了这种团结和变化？此外，这次经历对你们之后的比赛或者生活中的团队合作有什么积极的影响吗？"
                        }
                    ],
                    "timestamp": "2024-12-28T11:47:57.376379"
                },
                "recent_history": {
                    "value": [
                        {
                            "role": "assistant",
                            "content": "组队挑战高年级，这听起来就像是一个充满激情和挑战的故事。这种经历一定给你留下了深刻的印象。我想问问，你当时为什么会想要挑战高年级的同学呢？是出于对篮球的热爱，还是想要证明自己的能力？在挑战之前，你们团队是如何准备和练习的？在这个过程中，有没有什么特别难忘的瞬间或者感受？",
                            "timestamp": "2024-12-28T11:47:19.000902"
                        },
                        {
                            "role": "user",
                            "content": "挑战他们成功有一种成就感",
                            "timestamp": "2024-12-28T11:47:37.798143"
                        },
                        {
                            "role": "assistant",
                            "content": "感受到成就感是件非常美妙的事情，它能够增强自信心和团队精神。当你成功挑战高年级的团队时，那种成就感是如何体现出来的？你和你的队友们当时是怎样的心情？有没有庆祝胜利的特殊方式？此外，这次胜利对你的篮球生涯或者对你们团队的关系产生了什么影响吗？",
                            "timestamp": "2024-12-28T11:47:41.809405"
                        },
                        {
                            "role": "user",
                            "content": "我们更团结了",
                            "timestamp": "2024-12-28T11:47:55.054145"
                        },
                        {
                            "role": "assistant",
                            "content": "团结是一个团队成功的重要因素。听起来，这次挑战不仅增强了你们的技术和信心，还加深了你们之间的友谊和团队精神。你能分享一下，在这次挑战之后，你们是如何变得更加团结的？有没有什么具体的例子或者行动，体现了这种团结和变化？此外，这次经历对你们之后的比赛或者生活中的团队合作有什么积极的影响吗？",
                            "timestamp": "2024-12-28T11:47:57.376379"
                        }
                    ],
                    "timestamp": "2024-12-28T11:47:57.376379"
                }
            }
        }


# 创建全局实例
monitor_pool = MonitorPool()
