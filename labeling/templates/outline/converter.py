"""
提纲提取数据转换器模块

提供从 LLM 日志记录提取和转换数据的功能。

支持的功能：
- 从 LLM 日志中提取 prompt、answer、model、reasoning 等字段
- 批量转换多条日志记录
- 支持多种模型名称字段格式（model, used_model）
- 自动添加元数据（file_key, timestamp, model）
- 处理缺失字段，返回 None 以跳过无效记录
"""

import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime


class OutlineDataConverter:
    """
    提纲提取数据转换器

    用于将 LLM 调用日志记录转换为标注数据格式。

    典型的日志记录格式：
    {
        "file_key": "abc123",
        "timestamp": "2026-02-16T10:30:00",
        "success": true,
        "response": {
            "prompt": "原始文本内容...",
            "answer": "LLM 生成的回答",
            "model": "gpt-4",
            "used_model": "gpt-4",  # 或使用此字段
            "reasoning": "推理过程..."
        }
    }

    转换后的标注数据格式：
    {
        "prompt": "原始文本内容...",
        "answer": "LLM 生成的回答",
        "model": "gpt-4",
        "reasoning": "推理过程...",
        "metadata": {
            "file_key": "abc123",
            "timestamp": "2026-02-16T10:30:00",
            "model": "gpt-4"
        }
    }
    """

    # 支持的模型名称字段
    MODEL_FIELDS = ['model', 'used_model']

    # 必需的数据字段
    REQUIRED_DATA_FIELDS = ['prompt', 'answer']

    # 可选的数据字段
    OPTIONAL_DATA_FIELDS = ['thinking']

    def __init__(self, strict: bool = False):
        """
        初始化数据转换器

        Args:
            strict: 是否严格模式
                - True: 缺失必需字段时抛出异常
                - False: 缺失必需字段时返回 None
        """
        self.strict = strict

    def extract_model(self, record: Dict) -> Optional[str]:
        """
        从日志记录中提取模型名称

        支持多种字段名称：model, used_model

        Args:
            record: 日志记录

        Returns:
            模型名称，如果未找到则返回 None

        Example:
            >>> converter = OutlineDataConverter()
            >>> converter.extract_model({'response': {'model': 'gpt-4'}})
            'gpt-4'

            >>> converter.extract_model({'response': {'used_model': 'claude'}})
            'claude'
        """
        response_data = record.get('response')
        if not response_data or not isinstance(response_data, dict):
            return None

        # 尝试从多个可能的字段中获取模型名称
        for field_name in self.MODEL_FIELDS:
            model = response_data.get(field_name)
            if model:
                return model

        return None

    def extract_from_log(self, record: Dict) -> Optional[Dict]:
        """
        从 LLM 日志记录中提取标注数据

        提取的字段：
        - prompt: 原始文本内容（必需）
        - answer: LLM 生成的回答（必需）
        - model: 模型名称
        - reasoning: 推理过程（可选）

        同时添加元数据：
        - file_key: 文件标识
        - timestamp: 时间戳
        - model: 模型名称

        Args:
            record: LLM 日志记录

        Returns:
            包含提取数据的字典，如果记录无效则返回 None

        Raises:
            ValueError: 当 strict=True 且记录无效时

        Example:
            >>> converter = OutlineDataConverter()
            >>> log_record = {
            ...     'file_key': 'abc123',
            ...     'timestamp': '2026-02-16T10:30:00',
            ...     'success': True,
            ...     'response': {
            ...         'prompt': '原始文本',
            ...         'answer': 'LLM 回答',
            ...         'model': 'gpt-4',
            ...         'reasoning': '推理过程'
            ...     }
            ... }
            >>> data = converter.extract_from_log(log_record)
            >>> data['answer']
            'LLM 回答'
        """
        # 检查记录是否成功
        if not record.get('success'):
            if self.strict:
                raise ValueError("记录未成功处理 (success=False)")
            return None

        # 获取 response 数据
        response_data = record.get('response')
        if not response_data or not isinstance(response_data, dict):
            if self.strict:
                raise ValueError("response 字段缺失或不是字典类型")
            return None

        # 提取必需字段
        extracted_data: Dict[str, Any] = {}
        missing_fields: List[str] = []

        for field_name in self.REQUIRED_DATA_FIELDS:
            value = response_data.get(field_name)
            if value is None:
                missing_fields.append(field_name)
            else:
                extracted_data[field_name] = value

        # 检查必需字段是否完整
        if missing_fields:
            if self.strict:
                raise ValueError(f"缺少必需字段: {', '.join(missing_fields)}")
            return None

        # 提取可选字段
        for field_name in self.OPTIONAL_DATA_FIELDS:
            value = response_data.get(field_name)
            if value is not None:
                extracted_data[field_name] = value

        # 提取模型名称
        model = self.extract_model(record)
        if model:
            extracted_data['model'] = model

        # 添加元数据
        metadata: Dict[str, Any] = {}

        file_key = record.get('file_key')
        if file_key:
            metadata['file_key'] = file_key

        timestamp = record.get('timestamp')
        if timestamp:
            metadata['timestamp'] = timestamp

        if model:
            metadata['model'] = model

        # 如果有元数据，添加到结果中
        if metadata:
            extracted_data['metadata'] = metadata

        return extracted_data

    def convert_batch(self, records: List[Dict]) -> List[Dict]:
        """
        批量转换 LLM 日志记录

        自动跳过无效记录（返回 None 的记录）

        Args:
            records: LLM 日志记录列表

        Returns:
            转换后的标注数据列表

        Example:
            >>> converter = OutlineDataConverter()
            >>> records = [
            ...     {'file_key': 'abc', 'success': True, 'response': {...}},
            ...     {'file_key': 'def', 'success': False, 'response': {...}}
            ... ]
            >>> results = converter.convert_batch(records)
            >>> len(results)  # 只包含成功的记录
            1
        """
        results = []

        for i, record in enumerate(records):
            try:
                converted = self.extract_from_log(record)
                if converted is not None:
                    results.append(converted)
            except ValueError as e:
                # 在非严格模式下，继续处理下一条记录
                if not self.strict:
                    continue
                raise

        return results

    def convert_batch_with_stats(self, records: List[Dict]) -> Dict[str, Any]:
        """
        批量转换 LLM 日志记录，并返回统计信息

        Args:
            records: LLM 日志记录列表

        Returns:
            包含转换结果和统计信息的字典：
            {
                'data': List[Dict],  # 转换后的数据
                'stats': {
                    'total': int,      # 总记录数
                    'success': int,    # 成功转换数
                    'skipped': int,    # 跳过数
                    'success_rate': float  # 成功率
                }
            }

        Example:
            >>> converter = OutlineDataConverter()
            >>> result = converter.convert_batch_with_stats(records)
            >>> result['stats']['success_rate']
            0.85
        """
        total = len(records)
        successful = 0
        skipped = 0

        converted_data = []

        for record in records:
            try:
                converted = self.extract_from_log(record)
                if converted is not None:
                    converted_data.append(converted)
                    successful += 1
                else:
                    skipped += 1
            except ValueError:
                skipped += 1
                if self.strict:
                    raise

        success_rate = successful / total if total > 0 else 0.0

        return {
            'data': converted_data,
            'stats': {
                'total': total,
                'success': successful,
                'skipped': skipped,
                'success_rate': round(success_rate, 4)
            }
        }

    def validate_extracted_data(self, data: Dict) -> bool:
        """
        验证提取的数据是否有效

        Args:
            data: 提取的数据字典

        Returns:
            如果数据有效返回 True，否则返回 False

        Example:
            >>> converter = OutlineDataConverter()
            >>> converter.validate_extracted_data({
            ...     'prompt': 'text',
            ...     'answer': 'answer'
            ... })
            True
        """
        # 检查必需字段
        for field_name in self.REQUIRED_DATA_FIELDS:
            if field_name not in data or data[field_name] is None:
                return False

        return True

    def add_custom_metadata(
        self,
        data: Dict,
        custom_metadata: Dict[str, Any]
    ) -> Dict:
        """
        为提取的数据添加自定义元数据

        Args:
            data: 提取的数据字典
            custom_metadata: 要添加的自定义元数据

        Returns:
            更新后的数据字典

        Example:
            >>> converter = OutlineDataConverter()
            >>> data = {'prompt': 'text', 'answer': 'answer'}
            >>> converter.add_custom_metadata(data, {'batch_id': 1})
            {'prompt': 'text', 'answer': 'answer', 'metadata': {'batch_id': 1}}
        """
        # 创建数据副本以避免修改原始数据
        result = data.copy()

        if 'metadata' not in result:
            result['metadata'] = {}

        result['metadata'].update(custom_metadata)

        return result
