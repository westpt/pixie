"""
Agent核心层单元测试
测试BaseAgent和QAAssistant的功能
"""

import unittest
import time
from unittest.mock import Mock, patch, MagicMock
import threading
from agent_core.base_agent import BaseAgent, AgentState, AgentError, AgentStateError, AgentNotReadyError
from agent_core.qa_agent import QAAssistant, LLMAPIError


class TestAgentState(unittest.TestCase):
    """测试Agent状态枚举"""

    def test_state_values(self):
        """测试状态值"""
        self.assertEqual(AgentState.UNINITIALIZED.value, "uninitialized")
        self.assertEqual(AgentState.CREATED.value, "created")
        self.assertEqual(AgentState.RUNNING.value, "running")
        self.assertEqual(AgentState.STOPPED.value, "stopped")
        self.assertEqual(AgentState.DESTROYED.value, "destroyed")

    def test_state_string_representation(self):
        """测试状态字符串表示"""
        self.assertEqual(str(AgentState.RUNNING), "running")
        self.assertEqual(repr(AgentState.RUNNING), "AgentState.RUNNING")


class TestBaseAgent(unittest.TestCase):
    """测试BaseAgent基础类"""

    def setUp(self):
        """测试前准备"""
        self.agent_id = 1
        self.agent_name = "测试Agent"
        self.agent_type = "test_type"
        self.config = {
            "param1": "value1",
            "param2": "value2"
        }

    def test_initialization(self):
        """测试Agent初始化"""
        agent = MockAgent(self.agent_id, self.agent_name, self.agent_type, self.config)

        self.assertEqual(agent.agent_id, self.agent_id)
        self.assertEqual(agent.name, self.agent_name)
        self.assertEqual(agent.type, self.agent_type)
        self.assertEqual(agent.config, self.config)
        self.assertEqual(agent.state, AgentState.UNINITIALIZED)
        self.assertFalse(agent.is_running)
        self.assertFalse(agent.is_stopped)
        self.assertFalse(agent.is_destroyed)

    def test_create(self):
        """测试创建Agent"""
        agent = MockAgent(self.agent_id, self.agent_name, self.agent_type, self.config)

        agent.create()
        self.assertEqual(agent.state, AgentState.CREATED)
        self.assertIsNotNone(agent._created_at)

    def test_start(self):
        """测试启动Agent"""
        agent = MockAgent(self.agent_id, self.agent_name, self.agent_type, self.config)
        agent.create()

        agent.start()
        self.assertEqual(agent.state, AgentState.RUNNING)
        self.assertTrue(agent.is_running)
        self.assertIsNotNone(agent._started_at)

    def test_stop(self):
        """测试停止Agent"""
        agent = MockAgent(self.agent_id, self.agent_name, self.agent_type, self.config)
        agent.create()
        agent.start()

        agent.stop()
        self.assertEqual(agent.state, AgentState.STOPPED)
        self.assertTrue(agent.is_stopped)
        self.assertFalse(agent.is_running)
        self.assertIsNotNone(agent._stopped_at)

    def test_restart(self):
        """测试重启Agent"""
        agent = MockAgent(self.agent_id, self.agent_name, self.agent_type, self.config)
        agent.create()
        agent.start()

        # 重启
        agent.restart()
        self.assertEqual(agent.state, AgentState.RUNNING)
        self.assertTrue(agent.is_running)

    def test_destroy(self):
        """测试销毁Agent"""
        agent = MockAgent(self.agent_id, self.agent_name, self.agent_type, self.config)
        agent.create()
        agent.start()

        agent.destroy()
        self.assertEqual(agent.state, AgentState.DESTROYED)
        self.assertTrue(agent.is_destroyed)
        self.assertIsNotNone(agent._destroyed_at)

    def test_destroy_when_running(self):
        """测试运行中销毁Agent"""
        agent = MockAgent(self.agent_id, self.agent_name, self.agent_type, self.config)
        agent.create()
        agent.start()

        # 运行中销毁应该自动停止
        agent.destroy()
        self.assertEqual(agent.state, AgentState.DESTROYED)

    def test_invalid_state_transition(self):
        """测试非法状态转换"""
        agent = MockAgent(self.agent_id, self.agent_name, self.agent_type, self.config)
        agent.create()

        # 从CREATED不能直接到STOPPED，必须先RUNNING
        with self.assertRaises(AgentStateError):
            agent._set_state(AgentState.STOPPED)

    def test_destroyed_state_transitions(self):
        """测试已销毁状态不能转换"""
        agent = MockAgent(self.agent_id, self.agent_name, self.agent_type, self.config)
        agent.create()
        agent.destroy()

        # 已销毁的状态不能进行任何转换
        with self.assertRaises(AgentStateError):
            agent._set_state(AgentState.CREATED)

        with self.assertRaises(AgentStateError):
            agent.start()

        with self.assertRaises(AgentStateError):
            agent.stop()

    def test_get_status(self):
        """测试获取状态信息"""
        agent = MockAgent(self.agent_id, self.agent_name, self.agent_type, self.config)
        agent.create()

        status = agent.get_status()
        self.assertEqual(status['agent_id'], self.agent_id)
        self.assertEqual(status['name'], self.agent_name)
        self.assertEqual(status['type'], self.agent_type)
        self.assertEqual(status['state'], AgentState.CREATED.value)
        self.assertIn('task_statistics', status)

    def test_task_statistics(self):
        """测试任务统计"""
        agent = MockAgent(self.agent_id, self.agent_name, self.agent_type, self.config)
        agent.create()
        agent.start()

        stats = agent.task_statistics
        self.assertEqual(stats['total'], 0)
        self.assertEqual(stats['successful'], 0)
        self.assertEqual(stats['failed'], 0)

        # 模拟成功任务
        agent._total_tasks = 10
        agent._successful_tasks = 8
        agent._failed_tasks = 2

        stats = agent.task_statistics
        self.assertEqual(stats['total'], 10)
        self.assertEqual(stats['successful'], 8)
        self.assertEqual(stats['failed'], 2)
        self.assertEqual(stats['success_rate'], 0.8)

    def test_state_change_callback(self):
        """测试状态变化回调"""
        agent = MockAgent(self.agent_id, self.agent_name, self.agent_type, self.config)

        callback_called = []
        def callback(agent_obj, old_state, new_state):
            callback_called.append((old_state, new_state))

        agent.register_state_change_callback(callback)
        agent.create()
        agent.start()

        self.assertEqual(len(callback_called), 2)
        self.assertEqual(callback_called[0][0], AgentState.UNINITIALIZED)
        self.assertEqual(callback_called[0][1], AgentState.CREATED)
        self.assertEqual(callback_called[1][0], AgentState.CREATED)
        self.assertEqual(callback_called[1][1], AgentState.RUNNING)

    def test_process_task_when_not_ready(self):
        """测试未就绪时处理任务"""
        agent = MockAgent(self.agent_id, self.agent_name, self.agent_type, self.config)

        task = {
            'task_id': 'test_001',
            'content': '测试任务'
        }

        with self.assertRaises(AgentNotReadyError):
            agent.process_task(task)

    def test_process_task_success(self):
        """测试成功处理任务"""
        agent = MockAgent(self.agent_id, self.agent_name, self.agent_type, self.config)
        agent.create()
        agent.start()

        task = {
            'task_id': 'test_001',
            'content': '测试任务'
        }

        result = agent.process_task(task)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['content'], '测试结果')
        self.assertIn('execution_time', result)
        self.assertEqual(agent.task_statistics['total'], 1)
        self.assertEqual(agent.task_statistics['successful'], 1)

    def test_process_task_with_error(self):
        """测试任务处理错误"""
        agent = FailingAgent(self.agent_id, self.agent_name, self.agent_type, self.config)
        agent.create()
        agent.start()

        task = {
            'task_id': 'test_001',
            'content': '测试任务'
        }

        with self.assertRaises(AgentError):
            agent.process_task(task)

        # 验证失败统计
        self.assertEqual(agent.task_statistics['total'], 1)
        self.assertEqual(agent.task_statistics['failed'], 1)

    def test_validate_config(self):
        """测试配置验证"""
        agent = MockAgent(self.agent_id, self.agent_name, self.agent_type, self.config)
        self.assertTrue(agent.validate_config())

    def test_validate_empty_config(self):
        """测试空配置验证"""
        agent = MockAgent(self.agent_id, self.agent_name, self.agent_type, {})
        self.assertFalse(agent.validate_config())


class MockAgent(BaseAgent):
    """Mock Agent用于测试"""

    def __init__(self, agent_id, name, agent_type, config):
        super().__init__(agent_id, name, agent_type, config)
        self._execute_result = "测试结果"

    def _execute_task(self, task):
        """Mock任务执行"""
        return {
            'content': self._execute_result,
            'status': 'success',
            'format': 'text'
        }


class FailingAgent(BaseAgent):
    """会失败的Mock Agent用于测试错误处理"""

    def __init__(self, agent_id, name, agent_type, config):
        super().__init__(agent_id, name, agent_type, config)

    def _execute_task(self, task):
        """总是失败的任务执行"""
        raise Exception("模拟的任务执行失败")


class TestQAAssistant(unittest.TestCase):
    """测试QA助手Agent"""

    def setUp(self):
        """测试前准备"""
        self.agent_id = 1
        self.agent_name = "QA助手"
        self.agent_type = "qa_assistant"
        self.config = {
            'llm': {
                'provider': 'openai',
                'api_key': 'test-api-key',
                'api_endpoint': 'https://api.openai.com/v1/chat/completions',
                'model': 'gpt-3.5-turbo',
                'timeout': 30,
                'max_retries': 3
            },
            'max_history': 10
        }

    @patch('agent_core.qa_agent.requests.post')
    def test_initialization(self, mock_post):
        """测试QA助手初始化"""
        agent = QAAssistant(self.agent_id, self.agent_name, self.agent_type, self.config)

        self.assertEqual(agent.name, self.agent_name)
        self.assertEqual(agent.type, self.agent_type)
        self.assertEqual(agent._provider, 'openai')
        self.assertEqual(agent._model, 'gpt-3.5-turbo')
        self.assertEqual(agent._api_key, 'test-api-key')
        self.assertEqual(len(agent._conversation_history), 0)

    @patch('agent_core.qa_agent.requests.post')
    def test_validate_qa_config_success(self, mock_post):
        """测试成功的配置验证"""
        agent = QAAssistant(self.agent_id, self.agent_name, self.agent_type, self.config)
        # 初始化时已经验证，如果没有异常则通过

    def test_validate_qa_config_missing_api_key(self):
        """测试缺少API Key的配置"""
        config = self.config.copy()
        config['llm']['api_key'] = ''

        with self.assertRaises(AgentError) as context:
            QAAssistant(self.agent_id, self.agent_name, self.agent_type, config)

        self.assertIn("API Key不能为空", str(context.exception))

    def test_validate_qa_config_missing_endpoint(self):
        """测试缺少API端点的配置"""
        config = self.config.copy()
        config['llm']['api_endpoint'] = ''

        with self.assertRaises(AgentError) as context:
            QAAssistant(self.agent_id, self.agent_name, self.agent_type, config)

        self.assertIn("API端点不能为空", str(context.exception))

    @patch('agent_core.qa_agent.requests.post')
    def test_build_api_request_openai(self, mock_post):
        """测试构建OpenAI API请求"""
        agent = QAAssistant(self.agent_id, self.agent_name, self.agent_type, self.config)

        # 添加一些历史消息
        agent._conversation_history = [
            {'role': 'user', 'content': '之前的问题'},
            {'role': 'assistant', 'content': '之前的回答'}
        ]

        request = agent._build_api_request("新的问题")

        self.assertEqual(request['model'], 'gpt-3.5-turbo')
        self.assertEqual(len(request['messages']), 3)
        self.assertEqual(request['messages'][0]['role'], 'user')
        self.assertEqual(request['messages'][1]['role'], 'assistant')
        self.assertEqual(request['messages'][2]['content'], '新的问题')

    @patch('agent_core.qa_agent.requests.post')
    def test_build_api_request_zhipu(self, mock_post):
        """测试构建通义千问API请求"""
        config = self.config.copy()
        config['llm']['provider'] = 'zhipu'

        agent = QAAssistant(self.agent_id, self.agent_name, self.agent_type, config)

        request = agent._build_api_request("测试问题")

        self.assertEqual(request['model'], 'gpt-3.5-turbo')
        self.assertIn('top_p', request)

    @patch('agent_core.qa_agent.requests.post')
    def test_update_conversation_history(self, mock_post):
        """测试更新对话历史"""
        agent = QAAssistant(self.agent_id, self.agent_name, self.agent_type, self.config)

        agent._update_conversation_history("用户问题", "助手回答")

        self.assertEqual(len(agent._conversation_history), 2)
        self.assertEqual(agent._conversation_history[0]['role'], 'user')
        self.assertEqual(agent._conversation_history[1]['role'], 'assistant')

        # 测试历史限制
        for i in range(15):
            agent._update_conversation_history(f"问题{i}", f"回答{i}")

        # 应该只保留最后10条对话（20条消息）
        self.assertLessEqual(len(agent._conversation_history), 20)

    @patch('agent_core.qa_agent.requests.post')
    def test_clear_conversation_history(self, mock_post):
        """测试清空对话历史"""
        agent = QAAssistant(self.agent_id, self.agent_name, self.agent_type, self.config)

        agent._conversation_history = [
            {'role': 'user', 'content': '问题1'},
            {'role': 'assistant', 'content': '回答1'}
        ]

        agent.clear_conversation_history()
        self.assertEqual(len(agent._conversation_history), 0)

    @patch('agent_core.qa_agent.requests.post')
    def test_get_conversation_history(self, mock_post):
        """测试获取对话历史"""
        agent = QAAssistant(self.agent_id, self.agent_name, self.agent_type, self.config)

        # 添加历史
        for i in range(5):
            agent._update_conversation_history(f"问题{i}", f"回答{i}")

        # 获取全部历史
        full_history = agent.get_conversation_history()
        self.assertEqual(len(full_history), 10)  # 5对问答 = 10条消息

        # 获取限制历史
        limited_history = agent.get_conversation_history(limit=4)
        self.assertEqual(len(limited_history), 4)

    @patch('agent_core.qa_agent.requests.post')
    def test_get_api_statistics(self, mock_post):
        """测试获取API统计"""
        agent = QAAssistant(self.agent_id, self.agent_name, self.agent_type, self.config)

        stats = agent.get_api_statistics()
        self.assertEqual(stats['total_calls'], 0)
        self.assertEqual(stats['provider'], 'openai')

        # 模拟一些API调用
        agent._api_call_count = 10
        agent._api_total_time = 5.0

        stats = agent.get_api_statistics()
        self.assertEqual(stats['total_calls'], 10)
        self.assertEqual(stats['average_time'], 0.5)


if __name__ == '__main__':
    unittest.main()
