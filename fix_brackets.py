#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复中文括号导致的语法错误"""

import re

# 读取文件
with open('agent_core/base_agent.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 替换所有中文括号
replacements = {
    '（': '(',
    '）': ')',
    '《': '<',
    '》': '>',
    '「': '"',
    '」': '"',
}

for chinese, english in replacements.items():
    content = content.replace(chinese, english)

# 替换多字节字符
content = re.sub(r'[（）]+', '()', content)

# 写回文件
with open('agent_core/base_agent.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("中文括号已修复")

