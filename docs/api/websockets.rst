WebSocket API
=============

港股量化交易系统提供WebSocket接口，支持实时数据推送和双向通信。

连接信息
--------

**WebSocket URL:**

.. code-block:: text

   ws://localhost:8001/api/v1/websocket

**协议版本:** v1

**连接认证:**

连接时需要携带Bearer Token：

.. code-block:: javascript

   const ws = new WebSocket(
     'ws://localhost:8001/api/v1/websocket',
     ['Authorization', 'Bearer <your-token>']
   );

消息格式
--------

所有WebSocket消息使用JSON格式：

**客户端发送:**

.. code-block:: json

   {
     "type": "subscribe",
     "channel": "market_data",
     "symbol": "0700.HK"
   }

**服务器推送:**

.. code-block:: json

   {
     "type": "market_data",
     "symbol": "0700.HK",
     "data": {
       "timestamp": 1701234567.89,
       "price": 352.0,
       "volume": 1000000
     }
   }

消息类型
--------

subscribe
~~~~~~~~~

订阅频道。

.. code-block:: json

   {
     "type": "subscribe",
     "channel": "market_data|agent_status|backtest_progress|alerts",
     "symbol": "0700.HK",
     "params": {}
   }

unsubscribe
~~~~~~~~~~~

取消订阅。

.. code-block:: json

   {
     "type": "unsubscribe",
     "channel": "market_data",
     "symbol": "0700.HK"
   }

ping
~~~~

心跳检查。

.. code-block:: json

   {
     "type": "ping",
     "timestamp": 1701234567.89
   }

推送频道
--------

market_data
~~~~~~~~~~~

市场数据实时推送。

**推送频率:** 实时（每秒最多10次）

**数据结构:**

.. code-block:: json

   {
     "type": "market_data",
     "symbol": "0700.HK",
     "data": {
       "timestamp": 1701234567.89,
       "price": 352.0,
       "open": 350.0,
       "high": 355.0,
       "low": 345.0,
       "volume": 1000000
     }
   }

agent_status
~~~~~~~~~~~~

智能体状态更新。

**推送频率:** 每30秒或状态变化时

**数据结构:**

.. code-block:: json

   {
     "type": "agent_status",
     "agent_id": "coordinator",
     "data": {
       "status": "running",
       "cpu_usage": 45.2,
       "memory_usage": 512.5,
       "task_queue_size": 3,
       "last_update": 1701234567.89
     }
   }

backtest_progress
~~~~~~~~~~~~~~~~~

回测进度更新。

**推送频率:** 回测进行中每10秒

**数据结构:**

.. code-block:: json

   {
     "type": "backtest_progress",
     "backtest_id": "bt_123456",
     "data": {
       "progress": 0.65,
       "current_date": "2022-06-15",
       "total_days": 1095,
       "completed_days": 711,
       "estimated_remaining": 1800
     }
   }

alerts
~~~~~~

系统告警推送。

**推送频率:** 实时（当有告警时）

**数据结构:**

.. code-block:: json

   {
     "type": "alerts",
     "data": {
       "level": "warning",
       "message": "内存使用率超过80%",
       "timestamp": 1701234567.89,
       "source": "monitoring"
     }
   }

示例代码
--------

JavaScript
~~~~~~~~~~

.. code-block:: javascript

   class QuantWebSocket {
     constructor(url, token) {
       this.url = url;
       this.token = token;
       this.ws = null;
       this.callbacks = {};
     }

     connect() {
       this.ws = new WebSocket(this.url, ['Authorization', `Bearer ${this.token}`]);

       this.ws.onopen = () => {
         console.log('WebSocket连接已建立');
         this.subscribe('agent_status');
       };

       this.ws.onmessage = (event) => {
         const message = JSON.parse(event.data);
         this.handleMessage(message);
       };

       this.ws.onerror = (error) => {
         console.error('WebSocket错误:', error);
       };

       this.ws.onclose = () => {
         console.log('WebSocket连接已关闭');
         setTimeout(() => this.connect(), 5000); // 自动重连
       };
     }

     subscribe(channel, symbol = null) {
       this.send({
         type: 'subscribe',
         channel,
         symbol
       });
     }

     send(message) {
       if (this.ws.readyState === WebSocket.OPEN) {
         this.ws.send(JSON.stringify(message));
       }
     }

     handleMessage(message) {
       const handler = this.callbacks[message.type];
       if (handler) {
         handler(message.data);
       }
     }

     on(type, callback) {
       this.callbacks[type] = callback;
     }
   }

   // 使用示例
   const ws = new QuantWebSocket('ws://localhost:8001/api/v1/websocket', token);
   ws.connect();

   ws.on('agent_status', (data) => {
     console.log('智能体状态更新:', data);
   });

Python
~~~~~~

.. code-block:: python

   import asyncio
   import websockets
   import json

   class QuantWebSocket:
       def __init__(self, url, token):
           self.url = url
           self.token = token
           self.ws = None
           self.callbacks = {}

       async def connect(self):
           headers = {'Authorization': f'Bearer {self.token}'}
           async with websockets.connect(self.url, extra_headers=headers) as ws:
               self.ws = ws
               await self.subscribe('agent_status')
               await self.listen()

       async def subscribe(self, channel, symbol=None):
           await self.send({
               'type': 'subscribe',
               'channel': channel,
               'symbol': symbol
           })

       async def send(self, message):
           await self.ws.send(json.dumps(message))

       async def listen(self):
           async for message in self.ws:
               data = json.loads(message)
               await self.handle_message(data)

       async def handle_message(self, message):
           handler = self.callbacks.get(message['type'])
           if handler:
               await handler(message['data'])

       def on(self, type, callback):
           self.callbacks[type] = callback

   # 使用示例
   async def main():
       ws = QuantWebSocket('ws://localhost:8001/api/v1/websocket', token)

       @ws.on('agent_status')
       async def handle_agent_status(data):
           print(f'智能体状态更新: {data}')

       await ws.connect()

   asyncio.run(main())

错误处理
--------

连接错误
~~~~~~~~

连接失败时，系统会：

1. 记录错误日志
2. 尝试自动重连（最多5次）
3. 通知客户端连接状态

消息错误
~~~~~~~~

无效消息格式：

.. code-block:: json

   {
     "type": "error",
     "error": "invalid_message_format",
     "detail": "消息必须是有效的JSON格式"
   }

不支持的消息类型：

.. code-block:: json

   {
     "type": "error",
     "error": "unsupported_message_type",
     "detail": "不支持的消息类型: unknown_type"
   }

认证失败：

.. code-block:: json

   {
     "type": "error",
     "error": "authentication_failed",
     "detail": "无效或过期的访问令牌"
   }

连接限制
--------

* 最大并发连接数：1000
* 消息频率：每秒最多100条
* 连接超时：30秒无活动自动断开
* 订阅数量：每个连接最多50个频道

最佳实践
--------

1. **连接管理**
   - 实现自动重连机制
   - 监听连接状态变化
   - 设置合理的超时时间

2. **消息处理**
   - 异步处理消息
   - 不要阻塞事件循环
   - 实现消息队列

3. **资源优化**
   - 及时取消不需要的订阅
   - 避免订阅过多频道
   - 合理设置心跳间隔

4. **错误处理**
   - 记录所有错误信息
   - 实现降级方案
   - 监控连接质量
