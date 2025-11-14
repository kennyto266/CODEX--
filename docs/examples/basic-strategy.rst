基础策略示例

本示例展示如何创建一个简单的移动平均交叉策略。

代码示例：

.. code-block:: python

   class MACrossoverStrategy:
       def __init__(self):
           self.name = 'MA策略'
       
       def generate_signals(self, data):
           # 生成交易信号
           return []

