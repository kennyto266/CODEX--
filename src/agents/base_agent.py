"""
AI代理基类
定义所有代理的通用接口和行为
"""

import asyncio
import aiohttp
from typing import Dict, Any, Optional, List
import logging
from abc import ABC, abstractmethod
from datetime import datetime

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """AI代理基类"""
    
    def __init__(self, cursor_api_key: str, base_url: str):
        self.cursor_api_key = cursor_api_key
        self.base_url = base_url
        self.agent_id: Optional[str] = None
        self.session: Optional[aiohttp.ClientSession] = None
    
    @property
    @abstractmethod
    def name(self) -> str:
        """代理名称"""
        pass
    
    @property
    @abstractmethod
    def icon(self) -> str:
        """代理图标"""
        pass
    
    @abstractmethod
    def generate_prompt(self, market_data: List[Dict[str, Any]]) -> str:
        """
        生成代理提示词
        
        Args:
            market_data: 市场数据
            
        Returns:
            提示词字符串
        """
        pass
    
    async def launch(self, market_data: List[Dict[str, Any]]) -> Optional[str]:
        """
        启动代理
        
        Args:
            market_data: 市场数据
            
        Returns:
            代理ID
        """
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            prompt = self.generate_prompt(market_data)
            
            data = {
                "prompt": {
                    "text": f"""
作为{self.name}，请分析以下港股数据：

{prompt}

请提供专业的分析结果，包括：
1. 详细的分析过程
2. 具体的投资建议
3. 风险提示
4. 预期收益评估

请以JSON格式输出结果。
"""
                },
                "source": {
                    "repository": "https://github.com/kennyto266/CODEX--",
                    "ref": "main"
                }
            }
            
            url = f"{self.base_url}/agents"
            headers = {
                "Authorization": f"Bearer {self.cursor_api_key}",
                "Content-Type": "application/json"
            }
            
            async with self.session.post(url, headers=headers, json=data, timeout=30) as response:
                if response.status == 201:
                    result = await response.json()
                    self.agent_id = result.get('id')
                    logger.info(f"代理 {self.name} 启动成功，ID: {self.agent_id}")
                    return self.agent_id
                else:
                    error_text = await response.text()
                    logger.error(f"代理 {self.name} 启动失败: {response.status} - {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"代理 {self.name} 启动出错: {e}")
            return None
    
    async def get_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        获取代理状态
        
        Args:
            agent_id: 代理ID
            
        Returns:
            代理状态信息
        """
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            url = f"{self.base_url}/agents/{agent_id}"
            headers = {"Authorization": f"Bearer {self.cursor_api_key}"}
            
            async with self.session.get(url, headers=headers, timeout=15) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"获取代理 {self.name} 状态失败: {response.status}")
                    return None
                    
        except Exception as e:
            logger.warning(f"获取代理 {self.name} 状态出错: {e}")
            return None
    
    async def get_conversation(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        获取代理对话
        
        Args:
            agent_id: 代理ID
            
        Returns:
            代理对话内容
        """
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            url = f"{self.base_url}/agents/{agent_id}/conversation"
            headers = {"Authorization": f"Bearer {self.cursor_api_key}"}
            
            async with self.session.get(url, headers=headers, timeout=15) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"获取代理 {self.name} 对话失败: {response.status}")
                    return None
                    
        except Exception as e:
            logger.warning(f"获取代理 {self.name} 对话出错: {e}")
            return None
    
    async def get_result(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        获取代理分析结果
        
        Args:
            agent_id: 代理ID
            
        Returns:
            代理分析结果
        """
        try:
            status = await self.get_status(agent_id)
            conversation = await self.get_conversation(agent_id)
            
            if status and conversation:
                return {
                    "agent_name": self.name,
                    "agent_icon": self.icon,
                    "agent_id": agent_id,
                    "status": status,
                    "conversation": conversation,
                    "last_updated": datetime.now().isoformat()
                }
            else:
                logger.warning(f"代理 {self.name} 结果不完整")
                return None
                
        except Exception as e:
            logger.error(f"获取代理 {self.name} 结果出错: {e}")
            return None
    
    async def close(self):
        """关闭HTTP会话"""
        if self.session:
            await self.session.close()
            self.session = None