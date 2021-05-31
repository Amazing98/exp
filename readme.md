# 安装
- 目前实验环境使用的microk8s
  - 直接使用snap安装microk8s
  - microk8s安装完成后需要`microk8s enable helm`启动helm
  - 一定记得再使用命令`microk8s enable dns`启动dns服务，不然启动会失败，这个很坑的
- openfaas安装文档
  - https://github.com/openfaas/faas-netes/blob/master/chart/openfaas/README.md
  - 使用helm进行自动安装
- microk8s问题
  - 不能直接使用docker镜像，可以采取两种方法解决
    - https://microk8s.io/docs/registry-images
    - https://microk8s.io/docs/registry-built-in
    - 本项目为了简单的测试部署，采用的方案1，没有搭建新的register
  - openfaas一直部署失败
    - 需要使用命令`microk8s enable dns`
    - 这个很重要，一定要启动


- 协议问题
  - 始终使用json作为序列化协议，要求函数输入输出为json，因此框架不用考虑序列化使用的encoding问题，所有的encoding由用户自行解决
  - 针对function内部
    - 输入格式,args_num代表个数，args代表输入数据，为一个dict，key为str，value为数据    
    - 其中key在为用户输入时，为`input`
    - key在为其他函数输入时，为str(function_num)，既函数编号的str版本
  ```json
  {
    "args_num": 1,
    "args":{
      "1":"data of 1"
    }
  }
  ```
   - 输出格式，要求输出为一个dict，由三个key组成，key为`output`，value为输出数据；key为status，描述状态；key为message，描述错误信息
  ```json
  {
    "output":"data of output",
    "status":"False",
    "message":""
  }
  ```
  - 针对用户的输入与输出
    - 用户的输入需要放在一个data字段中
  ```json
    {"data": "data of user"}
  ```
    - 用户的输出会放到 "output"中:
  ```json
  {
  "output": "Hello nihao", 
  "status": "success"
  }
  ```

- openFaaS Auth
  - 采用golang的basic auth
  - 针对k8s部署的openfaas，可以采用`echo $(kubectl -n openfaas get secret basic-auth -o jsonpath="{.data.basic-auth-password}" | base64 --decode)`命令获取对应key
  - 对应key需要编码后才能进行使用编码规则为`用户名:key`再进行base64编码
  - 如用户名为admin(默认的)，key为F3JnwN0HpcNF，需要编码的字段为`admin：F3JnwN0HpcNF`，编码后结果为`YWRtaW46RjNKbndOMEhwY05G`
  - 在请求时，需要带上header
    - header key为`Authorization`
    - header value为`空格Basic空格` + `你的token`
  - 举个例子`curl http://127.0.0.1:31112/system/functions -H "Authorization: Basic YWRtaW46RjNKbndOMEhwY05G"`
  - openfaas对应API可以通过`https://ericstoekl.github.io/faas/developer/swagger/`文档进入swagger进行查看，注意带auth啊