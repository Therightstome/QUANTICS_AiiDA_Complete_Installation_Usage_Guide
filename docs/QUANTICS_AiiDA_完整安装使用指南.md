# QUANTICS-AiiDA 完整安装使用指南

## 概述

本指南将帮助您从零开始安装和配置整个QUANTICS-AiiDA系统，包括：
- AiiDA的安装和配置
- hartree集群的连接设置
- QUANTICS软件的配置
- GUI界面的使用

**适用对象：** 完全没有使用过AiiDA和QUANTICS的新用户

---

## 第一部分：环境准备

### 1.1 系统要求

- **操作系统：** Linux/WSL2 Ubuntu 22.04或更高版本
- **Python：** 3.8或更高版本
- **网络：** 能够连接到hartree.chem.ucl.ac.uk

### 1.2 检查Python环境

```bash
python3 --version
pip3 --version
```

如果没有安装Python，请安装：
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

---

## 第二部分：AiiDA安装和配置

### 2.1 创建虚拟环境

```bash
# 创建虚拟环境
python3 -m venv aiida_env

# 激活虚拟环境
source aiida_env/bin/activate

# 升级pip
pip install --upgrade pip
```

### 2.2 安装AiiDA

```bash
# 安装AiiDA核心包
pip install aiida-core
```

### 2.3 安装和配置PostgreSQL数据库

```bash
# 安装PostgreSQL
sudo apt install postgresql postgresql-contrib

# 启动PostgreSQL服务
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 创建数据库用户
sudo -u postgres createuser -P aiida
# 输入密码时，建议使用简单密码如：aiida123

# 创建数据库
sudo -u postgres createdb -O aiida aiida_db
```

### 2.4 初始化AiiDA

```bash
# 初始化AiiDA（首次运行）
verdi quicksetup

# 按提示输入：
# Profile name: your.email like UCL ID
# Email: your.email@ucl.ac.uk
# First name: Your Name
# Last name: Your Last Name
# Institution: UCL
# Database backend: postgresql_psycopg2
# PostgreSQL hostname: localhost
# PostgreSQL port: 5432
# PostgreSQL database name: aiida_db
# PostgreSQL username: aiida
# PostgreSQL password: aiida123

# 验证安装
verdi status
```

### 2.5 启动AiiDA守护进程

```bash
# 启动守护进程
verdi daemon start

# 检查状态
verdi daemon status
```

---

## 第三部分：hartree集群配置

### 3.1 设置SSH密钥（如果还没有）

```bash
# 生成SSH密钥对
ssh-keygen -t rsa -b 4096

# 将公钥复制到hartree集群
ssh-copy-id your_username@hartree.chem.ucl.ac.uk

# 测试连接
ssh your_username@hartree.chem.ucl.ac.uk
```

### 3.2 配置AiiDA计算机

```bash
# 设置计算机
verdi computer setup

# 按提示输入：
# Computer label: hartree
# Hostname: hartree.chem.ucl.ac.uk
# Description: Hartree cluster at UCL
# Transport plugin: core.ssh
# Scheduler plugin: core.sge
# Work directory: /home/your_username/aiida_work
# Mpirun command: mpirun -np {tot_num_mpiprocs}
# Default number of CPUs per machine: 1

# 配置SSH连接
verdi computer configure core.ssh hartree

# 按提示输入：
# Username: your_username
# Port: 22
# Look for keys: True
# SSH key file: /home/your_local_username/.ssh/id_rsa
# SSH key passphrase: （如果有密码）
# Connection timeout: 60
# Allow agent: True
# SSH proxy jump: （留空）
# SSH proxy command: （留空）
# Compress: True
# GSS auth: False
# GSS kex: False
# GSS deleg_creds: False
# GSS host: hartree.chem.ucl.ac.uk
# Load system host keys: True
# Key policy: RejectPolicy

# 测试连接
verdi computer test hartree
```

### 3.3 验证计算机配置

配置完计算机后，运行以下验证命令：

```bash
# 测试计算机连接
verdi computer test hartree

# 显示计算机详细信息
verdi computer show hartree

# 列出所有配置的计算机
verdi computer list
```

`verdi computer list`的预期输出应该显示：
```
Report: List of configured computers
Report: Use 'verdi computer show COMPUTERLABEL' to display more detailed information
* hartree
* hartree-clean
* localhost
```

检查AiiDA进程状态：
```bash
# 列出所有进程（作业）
verdi process list -a
```

**额外的连接测试：**
测试直接SSH连接以确保网络连通性：
```bash
# 测试SSH连接和文件访问（将ucapjd1替换为你的用户名）
ssh ucapjd1@hartree.chem.ucl.ac.uk ls -l ~/aiida_run/test_upload.txt
```

此命令验证：
- SSH连接正常工作
- 你的凭据正确
- 你可以访问hartree文件系统

### 3.4 配置QUANTICS代码

```bash
# 设置QUANTICS代码
verdi code create core.code.installed

# 按提示输入：
# Label: quantics-hartree
# Computer: hartree
# Default calculation input plugin: （留空）
# Absolute path of executable: /home/agiussani/quantics-6-6-16/bin/binary/x86_64/quantics
# List of prepend text: （留空）
# List of append text: （留空）

# 验证代码设置
verdi code list
verdi code show quantics-hartree@hartree
```

---

## 第四部分：安装GUI界面依赖

### 4.1 安装PyQt5和其他GUI依赖

```bash
# 确保在aiida虚拟环境中
source aiida_env/bin/activate

# 安装PyQt5
pip install PyQt5

# 如果在WSL2中，需要安装X11支持
sudo apt install python3-pyqt5 python3-pyqt5.qtwidgets
```

### 4.2 图形界面配置

#### 原生Linux系统：
大多数Linux发行版都内置X11支持，无需额外配置。

#### WSL1（Windows Linux子系统第1版）：

**步骤1：在Windows上安装X服务器**

1. 下载并安装VcXsrv（免费、开源）：
   - 官方下载地址：https://sourceforge.net/projects/vcxsrv/

2. 使用以下设置启动VcXsrv：
   - 选择"Multiple windows"
   - 选择"Start no client"
   - 在"Extra settings"里勾选"Disable access control"（这样WSL1能直接连接）
   - 点击"Finish"
   - 托盘会出现VcXsrv图标，表示服务已在监听0.0.0.0:6000

**步骤2：在WSL1中设置DISPLAY环境变量**

打开WSL1终端并编辑`~/.bashrc`：
```bash
# 指定X服务器地址（WSL1下就是localhost）
echo 'export DISPLAY=localhost:0.0' >> ~/.bashrc
echo 'export LIBGL_ALWAYS_INDIRECT=1' >> ~/.bashrc

# 使之生效
source ~/.bashrc
```

**步骤3：测试X11连接**

安装并测试X11应用程序：
```bash
# 更新软件包列表
sudo apt update

# 安装X11测试应用程序
sudo apt install x11-apps -y

# 测试X11转发
xeyes
```

如果你在Windows桌面上看到两只小眼睛跟随鼠标动，说明X11转发正常。

**WSL1故障排除：**

如果`xeyes`显示"Error: Can't open display:"，在当前会话中手动设置环境变量：
```bash
export DISPLAY=localhost:0.0
export LIBGL_ALWAYS_INDIRECT=1
xeyes
```

**Windows防火墙配置：**
- 打开"Windows安全中心"→"防火墙和网络保护"→"高级设置"→"入站规则"
- 创建或找到一条规则：允许TCP端口6000的入站连接，作用对象选"任意"或"vEthernet (WSL)"网络

#### WSL2（Windows Linux子系统第2版）：

```bash
# 安装X11服务器支持
sudo apt install x11-apps

# 在WSL2中设置DISPLAY变量
echo 'export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk "{print \$2}"):0.0' >> ~/.bashrc
source ~/.bashrc
```

**WSL2用户注意：** 在Windows上需要安装X11服务器（如VcXsrv或X410）

#### Windows 11的替代方案：WSLg
如果你使用的是Windows 11并且有包含WSLg的最新WSL版本：
```powershell
# 更新WSL以启用WSLg
wsl --update
```
使用WSLg，GUI应用程序可以直接运行，无需额外安装X服务器。

---

## 第五部分：获取和配置QUANTICS GUI

### 5.1 获取GUI文件

确保您有以下文件在工作目录中：
- `quantics_gui_aiida.py` - QUANTICS专业GUI（支持本地和AiiDA模式）
- `quantics_aiida_integration.py` - AiiDA集成模块
- `quantics_local_runner.py` - 本地运行模块

**注意：** 我们使用的是集成版本的GUI，它同时支持本地执行和AiiDA集群执行两种模式。

### 5.2 测试AiiDA配置

```bash
# 在GUI目录中运行测试
python3 -c "
from quantics_aiida_integration import QuanticsAiidaIntegration
integration = QuanticsAiidaIntegration()
print('AiiDA配置测试：', integration.test_aiida_setup())
"
```

---

## 第六部分：使用GUI界面

### 6.1 启动QUANTICS专业GUI

```bash
# 激活虚拟环境
source aiida_env/bin/activate

# 确保AiiDA守护进程运行（如果要使用AiiDA模式）
verdi daemon status

# 启动QUANTICS专业GUI
python3 quantics_gui_aiida.py
```

### 6.2 选择执行模式

GUI启动后，您可以在两种执行模式之间选择：

**本地执行模式：**
- 适合快速测试和小规模计算
- 计算在本地机器上运行
- 不需要集群连接

**AiiDA工作流模式：**
- 适合大规模计算和生产任务
- 计算提交到hartree集群
- 支持工作流管理和数据溯源

---

## 第七部分：GUI界面使用说明

### 7.1 QUANTICS专业GUI界面功能

#### 主要组件：
1. **执行模式选择** - 在本地执行和AiiDA工作流之间选择
2. **配置面板** - 设置输入文件、工作流类型和运行参数
3. **分析工具面板** - 选择后处理分析工具
4. **计算日志面板** - 显示实时计算日志
5. **AiiDA监控面板** - 监控AiiDA任务状态（仅AiiDA模式）
6. **结果浏览面板** - 查看计算结果和输出文件

#### 基本使用流程：

**Step 1: 选择执行模式**
1. 选择"Local Execution"（本地执行）进行快速测试
2. 选择"AiiDA Workflow"（AiiDA工作流）进行集群计算

**Step 2: 配置基本设置**
1. **计算名称（Calculation Name）：** 为您的计算任务起一个有意义的名称
2. **工作流类型（Workflow Type）：** 选择MCTDH、vMCG或DD-vMCG
3. **QUANTICS可执行文件：** 通常默认为"quantics"
4. **工作目录：** 可选，指定计算运行目录

**Step 3: 选择输入文件**
1. 点击".inp file"的"Browse"按钮选择QUANTICS输入文件
2. 点击".op file"的"Browse"按钮选择算符文件
3. 如果是DD-vMCG工作流，还需要选择"DB folder"（数据库文件夹）

**Step 4: 配置分析工具（可选）**
1. 在"Post-processing Analysis"面板中选择需要的分析工具：
   - `rdcheck etot` - 检查总能量
   - `rdcheck spop` - 检查单粒子布居
   - `rdcheck natpop` - 检查自然布居
   - `rdgpop` - 网格布居分析
2. 对于`rdgpop`工具，可以设置：
   - **nz值：** 网格点数（默认：2）
   - **dof值：** 自由度编号（默认：1）
   - **显示命令行：** 是否显示详细命令

**Step 5: 提交计算**
1. 检查所有参数设置
2. 点击"Start Calculation"（本地模式）或"Submit to AiiDA"（AiiDA模式）
3. 计算开始运行或提交到集群

**Step 6: 监控计算状态**
- **本地模式：** 在日志面板中查看实时输出，进度条显示计算进度
- **AiiDA模式：** 在AiiDA监控面板中查看任务状态，包括CREATED、SUBMITTED、RUNNING、FINISHED等状态

**Step 7: 查看结果**
1. 计算完成后，在"Results Browser"面板中查看输出文件
2. 可以打开结果目录查看所有输出文件
3. 查看分析工具的结果（如果使用了分析工具）

### 7.2 常用操作

#### 本地模式操作
```
- 停止计算：点击"Stop Calculation"按钮
- 清除日志：点击"Clear Log"按钮
- 保存日志：点击"Save Log"按钮
- 刷新结果：点击"Refresh"按钮更新结果显示
- 打开结果目录：点击"Open Directory"按钮
```

#### AiiDA模式操作
```
- 刷新任务列表：点击"Refresh"按钮更新AiiDA任务状态
- 查看任务详情：点击任务行的"View"按钮
- 监控任务状态：在AiiDA监控面板中查看任务进度
```

#### 配置操作
```
- 保存配置：菜单 → File → Save Configuration
- 加载配置：菜单 → File → Load Configuration
- 新建计算：菜单 → File → New Calculation
```

---

## 第八部分：故障排除

### 8.1 常见问题

**问题1：AiiDA守护进程无法启动**
```bash
# 解决方案
verdi daemon stop
verdi daemon start
```

**问题2：无法连接到hartree集群**
```bash
# 测试SSH连接
ssh your_username@hartree.chem.ucl.ac.uk

# 重新配置计算机
verdi computer configure core.ssh hartree
```

**问题3：GUI无法启动**

原生Linux系统：
```bash
# 检查X11是否运行
echo $DISPLAY
xeyes  # 测试图形界面

# 如果DISPLAY为空，尝试设置：
export DISPLAY=:0.0
```

WSL2系统：
```bash
# 检查X11转发
echo $DISPLAY
xeyes  # 测试图形界面

# 重新设置DISPLAY变量
export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0.0
```

**问题4：任务提交失败**
```bash
# 检查AiiDA状态
verdi status

# 查看守护进程日志
verdi daemon logshow
```

### 8.2 日志文件位置

- **AiiDA日志：** `~/.aiida/daemon/log/`
- **任务日志：** 通过GUI的"Show Results"查看
- **系统日志：** `/var/log/`

---

## 第九部分：高级配置

### 9.1 性能优化

```bash
# 增加守护进程工作进程数
verdi daemon incr 4

# 设置更大的工作目录
verdi computer configure core.ssh hartree
# 修改Work directory为更大的存储空间
```

### 9.2 自定义分析工具

可以在`quantics_gui_aiida.py`中添加新的分析工具。找到`workflow_analysis_map`字典并添加新工具：

```python
# 在workflow_analysis_map字典中为特定工作流添加新工具
self.workflow_analysis_map = {
    'MCTDH': [
        ('rdcheck etot', 'Total energy check'),
        ('rdcheck spop', 'Single particle population'),
        ('rdcheck natpop 0 0', 'Natural potential analysis'),
        ('rdgpop', 'Grid population analysis'),
        ('your_new_tool', 'Your tool description')  # 添加新工具
    ],
    # ... 其他工作流类型
}
```

---

## 第十部分：维护和备份

### 10.1 数据库备份

```bash
# 导出AiiDA数据库
verdi archive create backup.aiida

# 恢复数据库
verdi archive import backup.aiida
```

### 10.2 定期维护

```bash
# 清理旧的任务数据
verdi calcjob cleanworkdir --older-than 30  # 清理30天前的工作目录

# 检查系统状态
verdi status
verdi daemon status
```

---

## 快速启动检查清单

使用前请确保以下项目都已完成：

- [ ] PostgreSQL数据库运行正常
- [ ] AiiDA profile配置完成（`verdi status`显示绿色）
- [ ] AiiDA守护进程运行（`verdi daemon status`显示运行中）
- [ ] hartree集群SSH连接正常（`verdi computer test hartree`成功）
- [ ] QUANTICS代码路径正确配置
- [ ] 虚拟环境已激活
- [ ] GUI依赖包已安装（PyQt5）
- [ ] X11转发设置正确（WSL2用户）或X11正常工作（原生Linux）

---

## 快速启动命令

使用以下命令快速启动QUANTICS专业GUI：

```bash
# 进入项目目录
cd ~/quantics_exercises/test

# 激活环境和启动GUI
source quantics_env.sh && python quantics_gui_aiida.py
```

这个命令会：
1. 激活虚拟环境
2. 设置QUANTICS环境变量
3. 启动专业GUI界面

---

## 技术支持

如果遇到问题，请检查：
1. 系统日志和错误信息
2. AiiDA官方文档：https://aiida.readthedocs.io/
3. QUANTICS用户手册
4. 联系系统管理员或开发团队

---

**最后更新：** 2024年12月
**版本：** 1.0
**作者：** QUANTICS-AiiDA开发团队 