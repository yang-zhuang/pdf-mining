# Troubleshooting 常见问题排查

## PyCharm Claude Code 插件 + Conda 冲突问题

### 问题描述

在 PyCharm 中安装 Claude Code 插件后，单击 Claude Code 图标启动终端时出现 conda 错误：

```
FileNotFoundError: [Errno 2] No such file or directory: 'C:\\Users\\xxx\\AppData\\Local\\Temp\\_MEIxxxxxx\\conda\\shell\\condabin\\conda-hook.ps1'
```

或

```
Failed to activate conda environment.
Please open Anaconda prompt, and run `D:\Ananconda3\_conda.exe init powershell` there.
```

### 根本原因

Claude Code 插件会尝试使用**临时打包的 conda**（位于 `Temp\_MEIxxxxxx` 目录），而不是系统安装的 Anaconda。这会导致 PowerShell 无法找到正确的 conda hook 文件。

### 解决方案

**方法二：直接使用 PowerShell 而不加载 conda（推荐）**

1. 打开 PyCharm 的 **Settings**（或 **Preferences**）
2. 导航至 **Tools** → **Terminal**
3. 将 **Shell path** 设置为：
   ```
   powershell.exe
   ```
4. 重启 PyCharm

### 手动激活 Conda

如果需要使用 conda 环境，可以在 PyCharm 终端中手动运行：

```powershell
D:\Ananconda3\Scripts\activate
```

或

```powershell
conda activate <环境名>
```

### 其他尝试过的方案（不推荐）

- **方法一**：运行 `conda init powershell` - 无法解决，因为插件使用的是临时 conda
- **方法三**：修改插件配置 - 某些版本的插件可能没有相关选项
