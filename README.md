# utils4py 
> 整理开发中经常用的一些python工具包，提高生产效率<br>
> 安装：
```bash
pip install -e git+ssh://git@gitlab.test2pay.com/rct/utils4j.git#egg=utils4j
```


## 1. 调试环境支持
> - 环境变量IS_DEBUG=1表示调试模式，其他表示生产环境；

## 2. 配置支持
> - 默认支持python ConfigParser解析，参考 utils4py.ConfUtils
> - 调试环境下，默认读取 conf_test 目录下配置；
> - 生产环境下，默认读取 conf 目录下配置；

## 3.数据源相关
### 3.1） mysql连接
> - 默认配置路径 conf(_test)/data_source/mysql.conf
> - 配置格式
>>```
>>[xxxxx]
>>host            =   localhost
>>port            =   3306
>>user            =   xxx
>>password        =   xxx
>>db              =   xxx
>>charset         =   utf8
>>time_zone       =   +4:00
>>```
> - 使用示例
>>```python
>>from utils4py.data import connect_mysql
>>db = connect_mysql("xxxxx")
>>```
> - 默认自动提交
> - 事务支持

### 3.2）redis连接
> - 默认配置路径 conf(_test)/data_source/redis.conf
> - 配置格式
>>```
>>[xxxxx]
>>host            =   localhost
>>port            =   3306
>>password        =   xxx
>>db              =   0
>>with_key_prefix = True #标识rediskey是否添加section前缀
>>```
> - 使用示例
>>```python
>>from utils4py.data import connect_redis
>>r = connect_redis("xxxxx")
>>```
> - 在原redis连接基础上进行代理包装，常用操作自动在将key打上前缀 `xxxxx:`

### 3.3）mongo连接
> - 默认配置路径 conf(_test)/data_source/mongo.conf
> - 配置格式
>>```
>>[xxxxx]
>>user        =   user
>>password    =   password
>>host        =   localhost:27017
>>db          =   test
>>params      =   readPreference=secondaryPreferred
>>```
> - 使用示例
>>```python
>>from utils4py.data import connect_mongo
>>r = connect_mongo("xxxxx")
>>```

### 3.3）rabbitmq client
> - 默认配置路径 conf(_test)/data_source/rabbitmq.conf
> - 配置格式
>>```
>>[xxxxx]
>>host        =   localhost
>>port        =   5672
>>user        =   user
>>password    =   password
>>queue       =   queuename
>>durable     =   True
>>is_delay      = True
>>delivery_mode = 2
>>```
> - 使用示例
>>```python
>>from utils4py.data import connect_rabbitmq
>>rabbit_client = connect_rabbitmq("conf_section")
>>#发送消息
>>rabbit_client.send('msggggggggg')
>>#获取消息
>>s = rabbit_client.recv_msg()
>>#消费成功，删除消息
>>rabbit_client.del_msg()
>>#消费失败，消息重新入队
>>rabbit_client.re_in_queue_msg()
>>```


## 4. 服务相关
### 4.1） flask服务
| 模块 | 功能说明 | 使用方法 |
| :---: | :--- | :--- |
| utils4py.flask_ext.server.AppServer | server默认实现 | 初始化filter_paths和route_paths, 服务启动后自动扫描并加载filter和路由 |
| utils4py.flask_ext.filter.BaseFilter | 所有filter基类 | 自定义filter继承此类，并实现before_request和after_request |
| utils4py.flask_ext.routes.BaseService | 所有flask路由具体执行者基类 | 继承此类，并实现抽象方法check_args和run |
| utils4py.flask_ext.routes.service_route | 路由装饰器 | 对路由具体执行者加上此装饰器，AppServer启动时会扫描route_paths下所有此装饰器注册的路由服务 |



## 5. 离线相关
### 5.1) 复杂多进程消费者
> 主要模块
```
| 模块 | 功能说明 | 使用方法 |
| :---: | :--- | :--- |
| utils4py.consume.MultiConsumer | 消费进程基类 | 继承并实现 init_queue 方法，并装饰各阶段功能函数 |
| utils4py.consume.Controller | 控制器 | 实例化并调用start方法，支持安全退出 |
```
> 需要自定义的功能函数装饰器
>>```python
>>例：
>>from queue import Queue
>>from utils4py.comsume import MultiConsumer, BasicConsumer
>>class MyMultiConsumer(MultiConsumer):
>>    def init_queue(self):
>>        return Queue()
>>    @BasicConsumer.D.prepare()
>>    def prepare1(self):
>>        #构造消息容器，此方法一般不用写，用默认的即可BasicConsumer.__default_prepare
>>        pass
>>    @BasicConsumer.D.after_pop()
>>    def after_pop1(self,model):
>>        print("预处理消息1")
>>    @BasicConsumer.D.after_pop()
>>    def after_pop2(self,model):
>>        print("预处理消息2")
>>    @BasicConsumer.D.execute()
>>    def exec(self,model):
>>        pass     
>>consumer = MyMultiConsumer()
>>consumer.start()
>>```

### 5.2）简单多进程消费
继承SimpleBasicConsumer，重写recv_msg 方法，按需重写exec、sucess、fail方法
>>```python
>>例：
>>import utils4py.comsume.simple_consume.SimpleBasicConsumer
>>class RabbitMQWorkQueueConsumer(SimpleBasicConsumer):
>>    def __init__(self,conf_section,**kwargs):
>>        SimpleBasicConsumer.__init__(self,**kwargs)
>>        self._rabbit_client = connect_rabbitmq(conf_section)
>>
>>    def recv_msg(self):
>>        return self._rabbit_client.recv_msg()
>>    def exec(self,model):
>>        print(model.raw_message)
>>        result = np.random.randint(0,2)
>>        return result
>>    def success(self,model):
>>        self._rabbit_client.del_msg()
>>    def fail(self,model):
>>        self._rabbit_client.re_in_queue_msg()
>>
>>consumer = RabbitMQWorkQueueConsumer('rabbitmq_section')
>>consumer_process = ComponetConsumerProcess(consumer)
>>consumer_process.start()
``
```
| 装饰器 | 功能 | 备注 |
| :---: | :--- | :--- |
| D.prepare | 准备函数，初始化model | 只能注册一个，如果不注册，则使用默认实现 | 
| D.after_pop | 从队列获取数据之后执行,一般可以准备现场,备份消息之类的,以便于处理失败后可以捞回 | 可以有多个或者没有，按照注册index顺序执行 |
| D.execute | 执行具体业务 | 可以有多个，按照index顺序执行 |
| D.success | 前面所有阶段没有异常视为成功，则执行对应函数 | 可以有多个，按照index顺序执行 |
| D.fail | 前面任何地方有异常则执行，可用于执行恢复消息后者通知报警 | 可以有多个，按照index顺序执行 |
```
## 3.日志相关相关
构造按时间分割日志文件的logger
>>```python
>>from utils4py.log.log import init_log_from_config
>>logger = init_log_from_config('filename')
>>logger.info('msg')
``
> - 配置格式
>>```
>>[Base]
>>PauseFile = ./pause
>>LogSwitch = False
>>log_dir = /data/logs/anubis_application_service/
>>log_file = data_agent
>log_level = DEBUG
``



---
## 附: 工具列表
| 模块        | 功能说明    |
| :--------: | :-------- |
| utils4py.env | 识别是否是调试环境，is_debug 函数 |
| utils4py.ConfUtils | 配置加载工具 |
| utils4py.TextUtils | 字符相关工具，to_string, json_loads, json_dumps | 
| utils4py.ErrUtils | 错误信息处理 |
| utils4py.ArgsChecker | 参数检查 |
| utils4py.scan | 包扫描 |


