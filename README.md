# ♟️ AlphaGo-Style 五子棋对弈平台 | AlphaGo-Style Gomoku Platform
> **Engineered by:** xiaopeng_he
> **Contact:** he_xp815@hotmail.com


## 🔬 系统概述 | System Overview

这是一套基于纯 CPU 算力与确定性数学推演构建的工业级五子棋分析系统。本项目放弃了需要庞大 GPU 算力的神经网络黑盒模型，转而将 **Minimax 极大极小搜索** 与 **Numpy 向量化卷积** 深度结合，在 Python 环境下榨干单核算力。
系统配备了非阻塞式的双轨全息分析桌面，并在底层引入了迭代加深、强迫步早停以及具备自我演化能力的“精神时光屋”哈希记忆库。

This is an industrial-grade Gomoku (Five-in-a-Row) analysis system built on pure CPU computational power and deterministic mathematical deduction. Abandoning the GPU-heavy neural network black-box models, this project deeply integrates **Minimax Search** with **Numpy Vectorized Convolutions** to maximize single-core performance in Python.
The system features a non-blocking dual-board holographic analysis dashboard, iterative deepening, forced-move early stopping, and a self-evolving "Hyperbolic Time Chamber" hash memory database.

---

## ⚙️ 核心物理架构 | Core Architecture

### 1. 双轨异步渲染台 (Dual-Board Dashboard)
* **左侧实战区 (Main Battlefield):** 绝对纯净的人类落子空间，附带标准战术坐标尺 (A-O, 1-15)。
* **右侧沙盘区 (Holographic Sandbox):** 上帝视角的 AI 思维投影，实时渲染探针雷达与胜率气泡。
* **时空防阻塞锁 (Version Locking):** 人类可以凭借直觉随时落子，系统通过**时间戳版本号**瞬间丢弃过期的计算线程，保证极速响应，绝不卡顿。

### 2. 迭代加深与量子扰动 (Iterative Deepening & Quantum Variance)
* 突破了传统 DFS 的盲区，AI 按照深度逐层向外扫荡，将思维震荡实时推送到界面的胜率折线图上。
* 在引擎评分相同的候选点中注入微小的高斯噪音，打破机械平衡，赋予 AI 面对复杂局面的“创新”发散能力。

### 3. AI 精神时光屋 (Self-Play Chamber & O(1) Memory)
* 独立的自我演化管道。AI 可在后台进行左右互搏，将耗费大量算力得出的复杂残局最优解，转化为绝对数字指纹 (Hash) 持久化存储到 `brain_memory.json`。实战中遇到相同指纹，时间复杂度直接降为 O(1)。

### 4. 强迫步截断与时空回溯 (Forced-Move Pruning & Undo System)
* **算力熔断:** 当系统在浅层扫描中发现“不堵就会死”的唯一求生路线时，立即切断冗余深度推演，瞬间落子。
* **时间回溯:** 支持使用 `Backspace` 键进行悔棋，系统将重置物理宇宙状态并销毁当前推理线程，方便玩家复盘不同的战术分支。

### 5. 赛后物理审查 (Match Report Generation)
* 战斗结束后，系统将自动在本地生成 Markdown 格式的复盘报告，客观评判对局中出现的“严重失误 (恶手)”与“绝妙一击 (妙手)”。

---

## 🛠️ 部署与启动协议 | Installation & Usage

本系统为 CPU 极限压榨模型，无需配置复杂的 CUDA 驱动。只需安装基础的科学计算库：

This system is optimized for CPU processing and does not require complex CUDA configurations. Simply install the required scientific libraries:

```bash
pip install pygame numpy scipy