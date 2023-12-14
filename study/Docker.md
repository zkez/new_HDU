# Docker

***

## 基本概念
* Docker镜像
> Docker镜像是一个特殊的文件系统，除了提供容器运行时所需的程序、库、资源、配置等文件外，还包含了一些为运行时准备的一些配置参数（如匿名卷、环境变量、用户等）。  
> 镜像不包含任何动态数据，其内容在构建之后也不会被改变。  
> 分层存储：镜像构建时，会一层层构建，前一层是后一层的基础。每一层构建完就不会再发生改变，后一层上的任何改变只发生在自己这一层。  
* Docker容器
> 镜像是静态的定义，容器是镜像运行时的实体。容器可以被创建、启动、停止、删除、暂停等。
> 按照 Docker 最佳实践的要求，容器不应该向其存储层内写入任何数据，容器存储层要保持无状态化。所有的文件写入操作，都应该使用 数据卷（Volume）、或者 绑定宿主目录。  
* Docker仓库
> 集中存储、分发镜像的服务。

***

## 使用Docker镜像  
* 获取镜像  
> 'docker pull [选项] [Docker Registry 地址[:端口号]/]仓库名[:标签]'
* 列出镜像  
> 'docker image ls'  
> 'docker system df' 查看镜像、容器、数据卷所占用的空间  
> 'docker image ls -a' 查看所有镜像（包含中间镜像层）  
* 删除镜像  
> 'docker image rm [选项] <镜像1>'

***

## 使用Dockerfile定制镜像
* FROM指定基础镜像
> 必备指令，且必须是第一条指令。
* RUN执行命令
> * shell格式
> * exec格式
>> 镜像构建时，一定要确保每一层只添加真正需要添加的东西，任何无关的东西都应该清理掉。
* 构建镜像
> 'docker build [选项] <上下文路径/URL/->'  
> 镜像构建上下文（Context）：（请执行查阅相关资料）
>> 直接用Git repo进行构建  
>> 用给定的tar压缩包构建  
>> 从标准输入中读取Dockerfile进行构建  
>> 从标准输入中读取上下文进行构建  
* 其他制作镜像的方法
> （请自行查询相关资料）
* 镜像的实现原理
> Docker使用Union FS（联合文件系统）技术，Union FS（Union File System）：一种分层、轻量级并且高性能的文件系统，它支持对文件系统的修改作为一次提交来一层层叠加，同时可以将不同目录挂载到同一个虚拟文件系统下（Docker镜像就是由多层文件系统联合组成）。  
* Dockerfile指令详解
> 1. COPY复制文件
> 2. ADD复制文件（所有的文件复制均使用COPY指令，ADD指令仅在需要自动解压缩的场合使用）  
> 3. CMD容器启动命令    
> 4. ENTRYPOINT入口点
> 5. ENV设置环境变量  
> （笔者还在学习中）

***

## 使用Docker容器
* 启动容器  
> 1. 新建并启动：'docker run [选项] <镜像> [命令] [参数]'
> 2. 启动已终止容器：'docker container start [选项] <容器ID或容器名>'  
* 后台运行
> 添加 -d 参数  
* 终止容器
> 'docker container stop [选项] <容器ID或容器名>'  
* 进入容器   
> 1. ‘docker attach [选项] <容器ID或容器名>’  
> 2. ‘docker exec [选项] <容器ID或容器名> [命令] [参数]'（推荐使用：exit不会导致容器终止）
* 导出容器
> 'docker export [选项] <容器ID或容器名>'  
* 导入容器快照
> 'docker import [选项] <文件|URL|- [仓库名[:标签]]>'  
* 删除容器
> 'docker container rm [选项] <容器ID或容器名>' 

***

## Docker仓库
1. 拉取镜像
> 通过 docker search 命令来查找官方仓库中的镜像，并利用 docker pull 命令来将它下载到本地.  
2. 推送镜像
> 在登录后通过 docker push 命令来将自己的镜像推送到 Docker Hub.  
* 私有仓库（自己搞）

*** 
 
## Docker数据管理
1. 数据卷
> 数据卷是一个可供一个或多个容器使用的特殊目录，它绕过 UFS，可以提供很多有用的特性：
> * 数据卷可以在容器之间共享和重用
> * 对数据卷的修改会立马生效
> * 对数据卷的更新，不会影响镜像
> * 数据卷默认会一直存在，即使容器被删除
> 1. 创建一个数据卷：'docker volume create [选项] <数据卷名>'
> 2. 启动一个挂载数据卷的容器：'docker run -it -v <数据卷名>:<容器目录> <镜像名> [命令] [参数]'
> 3. 查看数据卷的具体信息：'docker volume inspect [选项] <数据卷名>'
> 4. 删除数据卷：'docker volume rm [选项] <数据卷名>'
2. 挂载主机目录
> 1. 挂载一个主机目录作为数据卷：'docker run -it -v <主机目录>:<容器目录> <镜像名> [命令] [参数]'
> 2. 查看数据卷的具体信息：'docker volume inspect [选项] <数据卷名>'
> 3. 挂载一个本地主机文件作为数据卷：'docker run -it -v <主机文件>:<容器目录> <镜像名> [命令] [参数]'

***

## Docker网络
* 外部访问容器
> 1. 映射所有接口地址：'docker run -p <主机端口>:<容器端口> <镜像名> [命令] [参数]'
> 2. 映射到指定地址的指定端口：'docker run -p <主机IP>:<主机端口>:<容器端口> <镜像名> [命令] [参数]'
> 3. 映射到指定地址的任意端口：'docker run -p <主机IP>::<容器端口> <镜像名> [命令] [参数]'
> 4. 查看映射端口配置：'docker port <容器名> [私有端口[/协议]]'
* 容器互联
> 1. 创建一个网络：'docker network create [选项] <网络名>'
> 2. 连接到一个网络：'docker network connect [选项] <网络名> <容器名>'  
> 如果你有多个容器之间需要互相连接，推荐使用 Docker Compose。
* 配置DNS
> （请自行查资料）

***

## Docker使用命令具体参数
https://docs.docker.com/engine/reference/commandline/cli/

*** 

## 一般性的指南和建议  
* 容器应该是短暂的：可以停止和销毁容器，并且创建一个新容器并部署好所需的设置和配置工作量应该是极小的。  
* 使用.dockerignore文件：指定要忽略的文件和目录。  
* 使用多阶段构建  
* 避免安装不必要的包
* 一个容器只运行一个进程
* 镜像层数尽可能少
* 将多行参数排序：按字母顺序排序  
* 构建缓存  
 