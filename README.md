<!-- markdownlint-disable MD033 MD041 -->

<div align="center">
  <img alt="LOGO" src="./logo.jpg" width="100" height="96" />

## MMleo
基于全新架构的偶像梦幻祭2小助手。图像技术 + 模拟控制，解放双手！
由 [MaaFramework](https://github.com/MaaXYZ/MaaFramework) 强力驱动！
**先行测试版<u>ver0.3</u>**,目前已能在大部分情况下稳定运行自动星光演唱会功能
以`1~2`个miss为您节省每天`9*3~12*3`min的时间(`27~36`min)
**现在能支持基础的合成和提交订单了,算法改进ing。使用方法：进入合成页面，启动"合成游戏"任务**
</div>
<p align="center">
  <img alt="license" src="https://img.shields.io/github/license/KhazixW2/MaaGumballs">
  <img alt="Python" src="https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white">
  <img alt="platform" src="https://img.shields.io/badge/platform-Windows-blueviolet">
  <img alt="commit" src="https://img.shields.io/github/commit-activity/m/fictionalflaw/MMleo">
</p>
---

## 简介

**MMleo** 是由 fictionalflaw 开发的游戏自动化工具，旨在帮助玩家完成每日任务，如签到、领取奖励以及在**简单难度**下自动星光演唱会等。  
**注意：** 本项目仅提供每日任务及部分歌曲的自动化操作，不支持全自动打歌，部分功能仍在开发和完善中。  
**注意：** 本项目推荐使用mumu、雷电模拟器，其他模拟器可能无法支撑**自动星光演唱会**功能的运行~~比如夜神~~。


---
 ## 主要功能

- [x] 启动游戏
- [x] 领取月卡钻石
- [x] 协会日常
- [x] 领取日常奖励
- [x] 每日海选
  - [x] 招募一次
  - [x] 招募十次
  - [x] 招募百次
- [x] 检测打歌点位
- [x] 星光演唱会
      ：由于尊重游戏规则，该功能只支持简单模式下运行，请勿妄图挑战该难度以上模式（做不到的，会fail）
- [x] 合成游戏
      :可选是否使用药水资源箱

- [ ] **其他功能待开发、测试**
> **注意事项：**
> - 初次运行**星光演唱会**任务前务必先运行**检测打歌点位**任务。后续不更改打歌界面布局的情况下不必再次运行。
> - 目前**星光演唱会**任务并不支持BP、难度的识别和调整，因此在执行该任务前请确保歌曲难度为简单，普通歌曲的BP消耗选择为0BP/1BP。
> - 当前**检测打歌点位**任务未加入自动化流程，仅能在打歌界面运行。因此推荐用户按如下流程操作：1、随便选一首歌，调整难度到"简单"。2、进入打歌界面后点击右上角暂停按钮。3、运行**检测打歌点位**任务
## 如何使用
1. 点击链接下载最新[Release](https://github.com/fictionalflaw/MMleo/releases)包

2. 解压后双击`MFAAvalonia.exe`即可运行
   


### Windows

- 对于绝大部分用户，请下载 MMleo-win-x86_64.zip
- 若确定自己的电脑是 arm 架构，请下载 MMleo-win-aarch64.zip
- 请注意！Windows 的电脑几乎全都是 x86_64 的，可能占 99.999%，除非你非常确定自己是 arm，否则别下这个！_
- 解压后运行 MFAAvalonia.exe（图形化界面，推荐使用，老版本UI为MFAWPF.exe）或 MaaPiCli.exe（命令行）即可
- 
### macOS

- 若使用 Intel 处理器，请下载 `MMleo-macos-x86_64.zip`
- 若使用 M1, M2 等 arm 处理器，请下载 `MMleo-macos-aarch64.zip`
- 使用方式：

  ```bash
  chmod a+x MaaPiCli
  ./MaaPiCli
  ```
  
### Linux

~~用 Linux 的大佬应该不需要我教~~

## 图形化界面

- <span style="font-size:25px;">[MFAAvalonia](https://github.com/SweetSmellFox/MFAAvalonia/)</span>  
- 由社区大佬[SweetSmellFox](https://github.com/SweetSmellFox)编写的基于Avalonia的GUI,通过内置的MAAframework来直接控制任务流程  
- 打开本程序和模拟器后，先在右上方选择要控制的模拟器  
- 勾选想要执行的任务后**开始任务**，任务会顺序执行，所有任务都需要游戏为开启状态  
- 点击部分任务右方的设置，可以配置任务属性
## 注意事项

- 提示“应用程序错误”，一般是缺少运行库，请安装一下 [vc_redist](https://aka.ms/vs/17/release/vc_redist.x64.exe)
- 添加 `-d` 参数可跳过交互直接运行任务，如 `./MaaPiCli.exe -d`
- MAA framework 2.0 版本已支持 mumu 后台保活，会在 run task 时获取 mumu 最前台的 tab
- 基于mumu模拟器1920x1080 dpi280开发，其它模拟器或分辨率如遇到问题，可首先尝试上述配置
- 反馈问题请附上日志文件 `debug/maa.log`以及问题界面的截图，谢谢！
## Join us

- 交流反馈 QQ 群：961390173
- MaaFramework 开发交流 QQ 群: 595990173

## 免责声明

本软件开源、免费，仅供学习交流使用。若您遇到商家使用本软件进行代练并收费，可能是分发、设备或时间等费用，产生的费用、问题及后果与本软件无关。

**在使用过程中，MMleo 可能存在任何意想不到的 Bug，因 MMleo 自身漏洞、文本理解有歧义、异常操作导致的账号问题等开发组不承担任何责任，请在确保在阅读完用户手册、自行尝试运行效果后谨慎使用！**

  
## 鸣谢

本项目由 **[MaaFramework](https://github.com/MaaXYZ/MaaFramework)** 强力驱动！

感谢以下开发者对本项目作出的贡献:

[![Contributors](https://contrib.rocks/image?repo=fictionalflaw/MMleo)](https://github.com/fictionalflaw/MMleo/graphs/contributors)

## 赞助

<!-- markdownlint-disable MD045 -->
<a href="https://afdian.com/a/fictionalflaw">
  <img width="200" src="https://pic1.afdiancdn.com/static/img/welcome/button-sponsorme.png">
</a>



