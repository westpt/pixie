"""
QA助手Agent
实现问答助手Agent，继承BaseAgent
"""

import requests
import time
from typing import Dict, Any, Optional, List
from .base_agent import BaseAgent, AgentError


class LLMAPIError(AgentError):
    """大模型API错误"""
    pass


class QAAssistant(BaseAgent):
    """
    QA助手Agent
    使用大模型API处理问答任务
    """

    def __init__(self, agent_id: int, name: str, agent_type: str, config: Dict[str, Any]):
        """
        初始化QA助手
        :param agent_id: Agent ID
        :param name: Agent名称
        :param agent_type: Agent类型
        :param config: Agent配置
        """
        super().__init__(agent_id, name, agent_type, config)

        # 验证配置
        self._validate_qa_config()

        # LLM API配置
        self._llm_config = config.get('llm', {})
        self._provider = self._llm_config.get('provider', 'openai')
        self._api_key = self._llm_config.get('api_key', '')
        self._api_endpoint = self._llm_config.get('api_endpoint', '')
        self._model = self._llm_config.get('model', 'gpt-3.5-turbo')
        self._timeout = self._llm_config.get('timeout', 30)
        self._max_retries = self._llm_config.get('max_retries', 3)

        # 对话历史（短期记忆）
        self._conversation_history: List[Dict[str, Any]] = []
        self._max_history = config.get('max_history', 10)

        # 请求统计
        self._api_call_count = 0
        self._api_total_time = 0.0

        self._logger.info(f"QA助手初始化完成，模型: {self._model}")

    def _validate_qa_config(self):
        """
        验证QA助手配置
        :raises: AgentError 如果配置无效
        """
        required_fields = ['llm']
        for field in required_fields:
            if field not in self._config:
                raise AgentError(f"缺少必需的配置字段: {field}")

        llm_config = self._config['llm']
        if 'api_key' not in llm_config or not llm_config['api_key']:
            raise AgentError("LLM API Key不能为空")

        if 'api_endpoint' not in llm_config or not llm_config['api_endpoint']:
            raise AgentError("LLM API端点不能为空")

        if 'model' not in llm_config:
            raise AgentError("LLM模型不能为空")

        self._logger.info("QA助手配置验证通过")

    def _build_api_request(self, user_message: str) -> Dict[str, Any]:
        """
        构建API请求
        :param user_message: 用户消息
        :return: API请求字典
        """
        # 构建消息历史（最近N条）
        messages = [
            {
                "role": msg.get('role', 'user'),
                "content": msg.get('content', '')
            }
            for msg in self._conversation_history[-self._max_history:]
        ]

        # 添加当前用户消息
        messages.append({
            "role": "user",
            "content": user_message
        })

        # 根据provider构建请求
        if self._provider == 'openai':
            return {
                "model": self._model,
                "messages": messages,
                "temperature": self._llm_config.get('temperature', 0.7),
                "max_tokens": self._llm_config.get('max_tokens', 2000),
                "stream": False
            }
        elif self._provider == 'zhipu':
            # 通义千问格式
            return {
                "model": self._model,
                "messages": messages,
                "temperature": self._llm_config.get('temperature', 0.7),
                "top_p": self._llm_config.get('top_p', 0.9)
            }
        else:
            raise AgentError(f"不支持的LLM provider: {self._provider}")

    def _call_llm_api(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用大模型API
        :param request_data: 请求数据
        :return: API响应
        :raises: LLMAPIError 如果API调用失败
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}"
        }

        try:
            self._logger.info(f"调用LLM API: {self._api_endpoint}")
            start_time = time.time()

            response = requests.post(
                self._api_endpoint,
                json=request_data,
                headers=headers,
                timeout=self._timeout
            )

            execution_time = time.time() - start_time
            self._api_call_count += 1
            self._api_total_time += execution_time

            # 检查响应状态
            if response.status_code != 200:
                error_msg = f"API调用失败，状态码: {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f", 详情: {error_detail}"
                except:
                    pass
                raise LLMAPIError(error_msg)

            # 解析响应
            response_data = response.json()

            # 提取回答（兼容不同provider格式）
            if self._provider == 'openai':
                if 'choices' in response_data and len(response_data['choices']) > 0:
                    answer = response_data['choices'][0].get('message', {}).get('content', '')
                    usage = response_data.get('usage', {})
                else:
                    raise LLMAPIError("API响应格式错误：缺少choices字段")

            elif self._provider == 'zhipu':
                if 'choices' in response_data and len(response_data['choices']) > 0:
                    answer = response_data['choices'][0].get('message', {}).get('content', '')
                    usage = response_data.get('usage', {})
                else:
                    raise LLMAPIError("API响应格式错误：缺少choices字段")

            else:
                answer = ''
                usage = {}

            self._logger.info(
                f"API调用成功，耗时: {execution_time:.2f}秒, "
                f"回答长度: {len(answer)}字符"
            )

            return {
                'content': answer,
                'usage': usage,
                'execution_time': execution_time,
                'raw_response': response_data
            }

        except requests.exceptions.Timeout:
            raise LLMAPIError(f"API调用超时（{self._timeout}秒）")

        except requests.exceptions.ConnectionError as e:
            raise LLMAPIError(f"API连接失败: {str(e)}")

        except requests.exceptions.RequestException as e:
            raise LLMAPIError(f"API请求失败: {str(e)}")

        except Exception as e:
            raise LLMAPIError(f"未知错误: {str(e)}")

    def _call_llm_api_with_retry(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用大模型API（带重试）
        :param request_data: 请求数据
        :return: API响应
        """
        last_error = None

        for attempt in range(1, self._max_retries + 1):
            try:
                self._logger.info(f"API调用尝试 {attempt}/{self._max_retries}")
                return self._call_llm_api(request_data)

            except LLMAPIError as e:
                last_error = e
                self._logger.warning(f"API调用失败（尝试 {attempt}）: {str(e)}")

                if attempt < self._max_retries:
                    # 等待后重试
                    wait_time = min(2 ** attempt, 10)  # 指数退避，最大10秒
                    self._logger.info(f"等待 {wait_time}秒后重试...")
                    time.sleep(wait_time)
                else:
                    self._logger.error(f"所有重试失败")
                    break

        # 所有重试都失败
        raise LLMAPIError(f"API调用失败（已重试{self._max_retries}次）: {str(last_error)}")

    def _update_conversation_history(self, user_message: str, assistant_message: str):
        """
        更新对话历史
        :param user_message: 用户消息
        :param assistant_message: 助手回复
        """
        # 添加用户消息
        self._conversation_history.append({
            'role': 'user',
            'content': user_message
        })

        # 添加助手回复
        self._conversation_history.append({
            'role': 'assistant',
            'content': assistant_message
        })

        # 限制历史长度
        if len(self._conversation_history) > self._max_history * 2:
            self._conversation_history = self._conversation_history[-self._max_history * 2:]

        self._logger.debug(f"对话历史更新，当前长度: {len(self._conversation_history)}")

    def _execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行问答任务
        :param task: 任务信息
        :return: 执行结果
        """
        # 提取任务内容
        user_message = task.get('content', '').strip()
        task_id = task.get('task_id', 'unknown')

        if not user_message:
            raise AgentError("任务内容为空")

        self._logger.info(f"处理问答任务: {task_id}")

        # 构建API请求
        request_data = self._build_api_request(user_message)

        # 调用API（带重试）
        api_response = self._call_llm_api_with_retry(request_data)

        # 提取回答
        answer = api_response['content']
        execution_time = api_response['execution_time']
        usage = api_response.get('usage', {})

        # 更新对话历史
        self._update_conversation_history(user_message, answer)

        # 构建结果
        result = {
            'content': answer,
            'format': 'text',
            'execution_time': execution_time,
            'status': 'success',
            'usage': usage,
            'api_provider': self._provider,
            'model': self._model,
            'conversation_length': len(self._conversation_history)
        }

        self._logger.info(
            f"任务处理成功: {task_id}, "
            f"回答长度: {len(answer)}字符, "
            f"执行时间: {execution_time:.2f}秒"
        )

        return result

    def clear_conversation_history(self):
        """
        清空对话历史
        """
        self._conversation_history.clear()
        self._logger.info("对话历史已清空")

    def get_conversation_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取对话历史
        :param limit: 返回数量限制（None返回全部）
        :return: 对话历史列表
        """
        if limit is None:
            return self._conversation_history.copy()
        else:
            return self._conversation_history[-limit:]

    def get_api_statistics(self) -> Dict[str, Any]:
        """
        获取API调用统计
        :return: 统计信息
        """
        avg_time = self._api_total_time / self._api_call_count if self._api_call_count > 0 else 0.0

        return {
            'total_calls': self._api_call_count,
            'total_time': self._api_total_time,
            'average_time': avg_time,
            'conversation_history_length': len(self._conversation_history),
            'provider': self._provider,
            'model': self._model
        }

    def __repr__(self) -> str:
        return (
            f"QAAssistant(id={self._agent_id}, name='{self._name}', "
            f"type='{self._type}', state={self._state.value}, "
            f"model='{self._model}')"
        )

    def __str__(self) -> str:
        return f"{self._name} (QA助手, ID: {self._agent_id}, 状态: {self._state.value})"
