"""
QA助手Agent
继承BaseAgent，实现问答任务处理
"""

import logging
import time
from typing import Dict, Any
import requests

from agent_core.base_agent import BaseAgent, AgentStatus

logger = logging.getLogger(__name__)

class QAAssistant(BaseAgent):
    """
    QA助手Agent
    调用大模型API处理问答任务
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化QA助手
        :param config: Agent配置字典
        """
        super().__init__(config)
        
        # LLM配置
        llm_config = config.get('llm', {})
        self.llm_provider = llm_config.get('provider', 'openai')
        self.api_key = llm_config.get('api_key', '')
        self.api_endpoint = llm_config.get('api_endpoint', '')
        self.model = llm_config.get('model', 'gpt-3.5-turbo')
        self.timeout = llm_config.get('timeout', 30)
        self.max_retries = llm_config.get('max_retries', 3)
        
        # 对话上下文（短期记忆）
        self.conversation_history = []  # 对话历史列表
        self.max_history_size = 10  # 最多保留10轮对话
        
        # 验证配置
        self._validate_llm_config()
    
    def _validate_llm_config(self):
        """验证LLM配置"""
        if not self.api_key:
            raise ValueError("API Key不能为空")
        
        if not self.api_endpoint:
            raise ValueError("API端点不能为空")
        
        if not self.model:
            raise ValueError("模型名称不能为空")
        
        self.logger.info(f"LLM配置验证成功：provider={self.llm_provider}, model={self.model}")
    
    def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理问答任务
        :param task: 任务字典
        :return: 处理结果字典
        """
        task_id = task.get('task_id', 'unknown')
        content = task.get('content', '')
        task_type = task.get('task_type', 'sync')
        
        self.logger.info(f"开始处理任务：{task_id}")
        self.current_task = task_id
        
        start_time = time.time()
        
        try:
            # 调用大模型API
            answer = self._call_llm(content)
            
            # 计算执行时间
            execution_time = time.time() - start_time
            
            # 格式化结果
            result = {
                'content': answer,
                'format': 'text',
                'execution_time': round(execution_time, 2),
                'status': 'success'
            }
            
            # 更新对话历史
            self._update_conversation_history(content, answer)
            
            # 更新处理计数
            self._update_processed_count(True)
            
            self.logger.info(f"任务处理成功：{task_id}, 耗时：{execution_time:.2f}秒")
            
            return result
            
        except Exception as e:
            # 计算执行时间
            execution_time = time.time() - start_time
            
            # 返回错误结果
            result = {
                'content': f"任务处理失败：{str(e)}",
                'format': 'text',
                'execution_time': round(execution_time, 2),
                'status': 'failed'
            }
            
            # 更新处理计数
            self._update_processed_count(False)
            
            self.logger.error(f"任务处理失败：{task_id}, 错误：{str(e)}")
            
            return result
    
    def _call_llm(self, question: str) -> str:
        """
        调用大模型API
        :param question: 用户问题
        :return: 模型回答
        """
        # 构建消息历史
        messages = []
        
        # 添加系统提示（可选）
        if self.conversation_history:
            # 如果有对话历史，添加上下文
            messages.append({
                'role': 'system',
                'content': '你是一个AI助手，请根据之前的对话历史回答用户的问题。'
            })
        
        # 添加历史对话
        for turn in self.conversation_history[-5:]:  # 只保留最近5轮对话
            messages.extend([
                {'role': 'user', 'content': turn['question']},
                {'role': 'assistant', 'content': turn['answer']}
            ])
        
        # 添加当前问题
        messages.append({'role': 'user', 'content': question})
        
        # 调用API（带重试机制）
        for attempt in range(self.max_retries):
            try:
                return self._make_api_request(messages)
            except Exception as e:
                self.logger.warning(f"API调用失败（尝试 {attempt + 1}/{self.max_retries}）：{str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                else:
                    raise
    
    def _make_api_request(self, messages: list) -> str:
        """
        发起API请求
        :param messages: 消息列表
        :return: 模型回答
        """
        if self.llm_provider == 'openai':
            return self._call_openai_api(messages)
        elif self.llm_provider == 'qwen':
            return self._call_qwen_api(messages)
        else:
            raise ValueError(f"不支持的LLM提供商：{self.llm_provider}")
    
    def _call_openai_api(self, messages: list) -> str:
        """
        调用OpenAI API
        :param messages: 消息列表
        :return: 模型回答
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': self.model,
            'messages': messages,
            'temperature': 0.7,
            'max_tokens': 2000
        }
        
        response = requests.post(
            self.api_endpoint,
            headers=headers,
            json=data,
            timeout=self.timeout
        )
        
        response.raise_for_status()
        result = response.json()
        
        if 'choices' in result and len(result['choices']) > 0:
            return result['choices'][0]['message']['content']
        else:
            raise ValueError(f"API返回异常：{result}")
    
    def _call_qwen_api(self, messages: list) -> str:
        """
        调用通义千问API
        :param messages: 消息列表
        :return: 模型回答
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': self.model,
            'messages': messages,
            'temperature': 0.7,
            'max_tokens': 2000
        }
        
        response = requests.post(
            self.api_endpoint,
            headers=headers,
            json=data,
            timeout=self.timeout
        )
        
        response.raise_for_status()
        result = response.json()
        
        if 'output' in result and 'choices' in result['output'] and len(result['output']['choices']) > 0:
            return result['output']['choices'][0]['message']['content']
        else:
            raise ValueError(f"API返回异常：{result}")
    
    def _update_conversation_history(self, question: str, answer: str):
        """
        更新对话历史
        :param question: 用户问题
        :param answer: 模型回答
        """
        self.conversation_history.append({
            'question': question,
            'answer': answer,
            'timestamp': time.time()
        })
        
        # 限制历史大小
        if len(self.conversation_history) > self.max_history_size:
            self.conversation_history = self.conversation_history[-self.max_history_size:]
        
        self.logger.debug(f"对话历史更新：当前{len(self.conversation_history)}轮")
    
    def clear_conversation_history(self):
        """
        清空对话历史（开始新对话）
        """
        self.conversation_history = []
        self.logger.info("对话历史已清空")
    
    def get_conversation_history(self) -> list:
        """
        获取对话历史
        :return: 对话历史列表
        """
        return self.conversation_history
    
    def _on_start(self):
        """
        Agent启动时的回调
        """
        super()._on_start()
        self.logger.info(f"QA助手Agent启动：{self.name}")
    
    def _on_stop(self):
        """
        Agent停止时的回调
        """
        super()._on_stop()
        self.logger.info(f"QA助手Agent停止：{self.name}")

