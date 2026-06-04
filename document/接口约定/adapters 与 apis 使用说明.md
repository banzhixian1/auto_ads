# adapters 与 apis 使用说明

## 1. 适用范围

这两层职责不同：

- `apis`：直接请求外部服务
- `adapters`：做协议/格式转换

它们通常配合使用，但不要混用职责。

---

## 2. `src/apis`

当前主要文件：

- `llm.py`

### 2.1 `apis/llm.py`

#### 用途

封装对外部或本地 LLM 服务的直接调用。

#### 主要入口

- `inference(messages, model_name=None, timeout=None, orgin_result=False)`

#### 当前行为

- 默认使用配置中的本地 LLM 服务地址
- 根据 `model_name` 选择调用方式
- 通过 `requests_client` 发 HTTP 请求

#### 典型调用

```python
from src.apis.llm import inference

result = inference(messages=[...], model_name="Qwen3-VL-8B-Instruct")
```

#### 输入约定

- `messages`：消息列表
- `model_name`：模型名，可不传
- `timeout`：超时时间
- `orgin_result`：是否保留原始结果

#### 适合谁调用

- `services`
- 更高层的业务模块

#### 不适合谁直接调用

- 不建议把复杂业务 prompt 组装逻辑直接塞到 `apis/llm.py`
- 格式适配应先交给 `adapters/llm.py`

---

## 3. `src/adapters`

当前主要文件：

- `llm.py`
- `image.py`

### 3.1 `adapters/llm.py`

#### 用途

负责 LLM 输入输出的格式适配，尤其是消息结构和图片内容。

#### 主要函数

- `messages_to_contents(...)`
- `replace_images_in_contents(...)`
- `remove_mask_in_contents(...)`

#### 典型使用顺序

1. 准备标准 `messages`
2. 调 `messages_to_contents(...)`
3. 如果消息里有图片，再调 `replace_images_in_contents(...)`
4. 发请求前如需清理内部标记，再调 `remove_mask_in_contents(...)`

#### 适用场景

- 模型接口不直接接受当前业务消息结构
- 需要把 URL、本地路径、base64 图片转成统一的请求内容

#### 注意事项

- 它负责“格式适配”，不是模型调用入口
- 不应在这里承接 prompt 业务逻辑

---

### 3.2 `adapters/image.py`

#### 用途

统一图片读取、解码、编码与 base64 转换。

#### 主要函数

- `decode_image(image_str)`
- `image_to_base64(img)`
- `encode_image_Base64(image_str)`

#### 支持的图片输入

当前实现支持：

- HTTP/HTTPS URL
- 本地文件路径
- base64 字符串

#### 典型调用

```python
from src.adapters.image import decode_image, image_to_base64

image = decode_image(image_str)
image_b64 = image_to_base64(image)
```

#### 注意事项

- 图片适配逻辑优先放这里，不要把同样的解析逻辑散落到 `services` 或 `apis`
- 纯业务层通常不直接操作底层图片格式转换细节

---

## 4. `apis` 与 `adapters` 的推荐组合方式

### 4.1 推荐链路

对于 LLM 场景，推荐链路是：

1. 业务层准备输入
2. `adapters/llm.py` 做消息和图片格式适配
3. `apis/llm.py` 发请求
4. 业务层接收结果

### 4.2 不推荐做法

- 在 `apis/llm.py` 里直接塞复杂图片转换逻辑
- 在 `adapters` 里直接发请求
- 在 `services` 里重复手写格式转换，而不复用 adapter

---

## 5. 当前限制

- 当前 `apis/llm.py` 的能力主要围绕已有模型调用封装展开，未抽象成多供应商统一层
- `adapters/llm.py` 当前更多偏向图片和消息结构适配，后续如果模型协议增多，可继续扩
- `adapters/image.py` 是底层能力，不负责业务图像理解策略
