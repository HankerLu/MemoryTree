from typing import Dict, Any
import asyncio
import logging
from datetime import datetime
from utils.monitor_pool import monitor_pool  # 添加导入
from .node_types import (
    ConversationNode,
    NarrativeNode,
    SVGNode,
    AnalysisNode
)

logger = logging.getLogger(__name__)


class WorkflowThread:
    """工作流执行器：负责执行单个工作单元的处理流程"""

    def __init__(self):
        # 初始化所有节点
        self.narrative_node = NarrativeNode()
        self.svg_node = SVGNode()
        self.analysis_node = AnalysisNode()

    async def process(self, work_unit: Dict[str, Any], status_callback=None) -> Dict[str, Any]:
        """处理工作单元"""
        try:
            if not work_unit or "id" not in work_unit:
                raise ValueError("无效的工作单元：缺少ID")
                
            unit_id = work_unit["id"]
            logger.info(f"开始处理工作单元: {unit_id}")

            # 添加监控点：工作单元工作流状态
            await monitor_pool.record(
                category="system",
                key=unit_id+"_workflow_status",
                value={
                    "content": f"开始处理工作单元: {unit_id}"
                }
            )

            # 确保结果字典存在
            if "results" not in work_unit:
                work_unit["results"] = {}
            
            # 叙事生成阶段
            logger.info(f"开始生成叙事: {unit_id}")

            # 添加监控点：工作单元工作流状态
            await monitor_pool.record(
                category="system",
                key=unit_id + "_workflow_status",
                value={
                    "content": f"开始生成叙事: {unit_id}"
                }
            )

            work_unit["status"] = "generating_narrative"
            work_unit["node_states"]["narrative"] = {
                "status": "processing",
                "start_time": datetime.now().isoformat()
            }
            if status_callback:
                await status_callback(unit_id, {
                    "status": work_unit["status"],
                    "node_states": work_unit["node_states"]
                })
            
            # 叙事生成
            work_unit = await self.narrative_node.process(work_unit)
            work_unit["node_states"]["narrative"]["status"] = "completed"
            work_unit["node_states"]["narrative"]["end_time"] = datetime.now().isoformat()
            logger.info(f"叙事生成完成: {unit_id}")

            # 添加监控点：工作单元工作流状态
            await monitor_pool.record(
                category="system",
                key=unit_id + "_workflow_status",
                value={
                    "content": f"叙事生成完成: {unit_id}"
                }
            )

            if status_callback:
                await status_callback(unit_id, {
                    "node_states": work_unit["node_states"]
                })
            
            # SVG生成阶段
            logger.info(f"开始生成SVG: {unit_id}")

            # 开始分析叙述体
            logger.info(f"开始分析叙述体: {unit_id}")

            # 添加监控点：工作单元工作流状态
            await monitor_pool.record(
                category="system",
                key=unit_id + "_workflow_status",
                value={
                    "content": f"开始生成SVG和分析叙述体: {unit_id}"
                }
            )

            work_unit["status"] = "generating_svg"
            work_unit["node_states"]["svg"] = {
                "status": "processing",
                "start_time": datetime.now().isoformat()
            }
            if status_callback:
                await status_callback(unit_id, {
                    "status": work_unit["status"],
                    "node_states": work_unit["node_states"]
                })
            
            # 并行处理SVG和分析
            svg_task = asyncio.create_task(self.svg_node.process(work_unit.copy()))
            analysis_task = asyncio.create_task(self.analysis_node.process(work_unit.copy()))
            
            try:
                # 等待SVG结果
                svg_result = await svg_task
                if svg_result and "results" in svg_result:
                    work_unit["results"].update(svg_result["results"])
                    work_unit["status"] = "svg_completed"
                    work_unit["node_states"]["svg"]["status"] = "completed"
                    work_unit["node_states"]["svg"]["end_time"] = datetime.now().isoformat()
                    logger.info(f"SVG生成完成: {unit_id}")

                    # 添加监控点：工作单元工作流状态
                    await monitor_pool.record(
                        category="system",
                        key=unit_id + "_workflow_status",
                        value={
                            "content": f"SVG生成完成: {unit_id}"
                        }
                    )


                    if status_callback:
                        await status_callback(unit_id, {
                            "status": work_unit["status"],
                            "node_states": work_unit["node_states"]
                        })
                else:
                    logger.error(f"SVG生成失败: {unit_id}")

                    # 添加监控点：工作单元工作流状态
                    await monitor_pool.record(
                        category="system",
                        key=unit_id + "_workflow_status",
                        value={
                            "content": f"SVG生成失败: {unit_id}"
                        }
                    )


                    work_unit["status"] = "svg_failed"
                    work_unit["node_states"]["svg"]["status"] = "failed"
                    work_unit["node_states"]["svg"]["end_time"] = datetime.now().isoformat()
                    if status_callback:
                        await status_callback(unit_id, {
                            "status": work_unit["status"],
                            "node_states": work_unit["node_states"]
                        })
                    
            except Exception as e:
                logger.error(f"SVG生成异常: {str(e)}")

                # 添加监控点：工作单元工作流状态
                await monitor_pool.record(
                    category="system",
                    key=unit_id + "_workflow_status",
                    value={
                        "content": f"SVG生成异常: {str(e)}"
                    }
                )


                work_unit["status"] = "svg_failed"
                work_unit["node_states"]["svg"]["status"] = "failed"
                work_unit["node_states"]["svg"]["error"] = str(e)
                work_unit["node_states"]["svg"]["end_time"] = datetime.now().isoformat()
                if status_callback:
                    await status_callback(unit_id, {
                        "status": work_unit["status"],
                        "node_states": work_unit["node_states"]
                    })
            
            # 后台继续处理分析任务
            asyncio.create_task(self._complete_analysis(work_unit, analysis_task))
            
            return work_unit
            
        except Exception as e:
            logger.error(f"工作流处理失败: {str(e)}")

            # 添加监控点：工作单元工作流状态
            await monitor_pool.record(
                category="system",
                key=work_unit['id'] + "_workflow_status",
                value={
                    "content": f"工作流{work_unit['id']}处理失败: {str(e)}"
                }
            )


            if status_callback:
                await status_callback(unit_id, {
                    "status": "failed",
                    "error": str(e)
                })
            raise

    async def _complete_analysis(self, work_unit: Dict[str, Any], analysis_task: asyncio.Task):
        """后台完成分析任务"""
        try:
            analysis_result = await analysis_task
            work_unit["results"]["analysis"] = analysis_result
            work_unit["status"] = "completed"
            logger.info(f"分析任务完成: {work_unit['id']}")

            # 添加监控点：工作单元工作流状态
            await monitor_pool.record(
                category="system",
                key=work_unit['id'] + "_workflow_status",
                value={
                    "content": f"分析任务完成，工作流执行完成: {work_unit['id']}"
                }
            )

        except Exception as e:
            logger.error(f"分析任务失败: {str(e)}")

            # 添加监控点：工作单元工作流状态
            await monitor_pool.record(
                category="system",
                key=work_unit['id'] + "_workflow_status",
                value={
                    f"分析任务失败: {str(e)}"
                }
            )

            work_unit["status"] = "analysis_failed"
            work_unit["error"] = str(e)
