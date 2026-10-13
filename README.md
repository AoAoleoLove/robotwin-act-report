# RoboTwin × ACT 实验报告

**[点击这里完整阅读实验报告](https://aoaoleolove.github.io/robotwin-act-report/)**


完整的网页实验报告：10 个章节、训练曲线、6 段实验视频、原始日志与关键源文件快照。

## 在线阅读

本仓库使用 GitHub Pages 托管。发布后，在仓库首页右侧的 About / Website 或 Deployments 中点击网页地址，即可完整查看报告，无需下载或解压文件包。

## 发布配置

仓库 Settings → Pages → Build and deployment：

- Source：Deploy from a branch
- Branch：main
- Folder：/(root)

保存后等待 GitHub Pages 部署完成。根目录的 .nojekyll 会保留以下划线开头的附件，例如 source/envs/_base_task.py。

## 内容

- index.html、styles.css、report.js：报告正文、样式与交互。
- media/：6 段 MP4 与封面，可在网页内直接播放。
- figures/：训练曲线和诊断图。
- evidence/：原始日志、CSV 与验证结果。
- source/：关键英文源文件快照。
- experiment-summary.json：实验结果摘要。
- media-manifest.json：视频来源。
- package-manifest.json：文件校验值。

本仓库为实验报告与归档快照。复现命令中的绝对路径保留了实操记录；在其他电脑运行时需要替换为自己的工程路径。

## 本地阅读

使用浏览器打开 index.html 即可。保留其余文件和目录，以显示完整样式、图表和视频。
