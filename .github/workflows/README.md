# GitHub Actions 自动发布配置

## 功能说明

当推送以 `v` 开头的版本标签（如 `v0.0.4`）到 GitHub 时，会自动：
1. 构建 Python 包（wheel 和 sdist）
2. 检查包的有效性
3. 发布到 PyPI

## 配置步骤

### 1. 添加 PyPI API Token 到 GitHub Secrets

1. 访问 GitHub 仓库：https://github.com/all-for-freedom/scriptperf
2. 进入 **Settings** → **Secrets and variables** → **Actions**
3. 点击 **New repository secret**
4. 添加以下 secret：
   - **Name**: `PYPI_API_TOKEN`
   - **Value**: 你的 PyPI API Token（从 PyPI 账户设置中获取）
   
   **注意**：
   - Token 应该以 `pypi-` 开头
   - 从 https://pypi.org/manage/account/token/ 获取你的 API Token
   - **重要**：不要将 Token 直接写在代码或文档中，只存储在 GitHub Secrets 中！

### 2. 使用流程

#### 自动发布流程（推荐）

```bash
# 1. 更新代码并提交
git add .
git commit -m "更新功能"
git push

# 2. 更新 CHANGELOG.rst（可选但推荐）
# 在文件顶部添加新版本信息

# 3. 创建并推送版本标签（这会触发自动发布）
git tag v0.0.4
git push origin v0.0.4
```

推送标签后，GitHub Actions 会自动：
- ✅ 构建包
- ✅ 检查包
- ✅ 发布到 PyPI

#### 手动触发

如果需要手动触发发布，可以：
1. 访问 GitHub 仓库的 **Actions** 标签页
2. 选择 **Publish to PyPI** 工作流
3. 点击 **Run workflow**

## 注意事项

1. **标签格式**：必须使用 `v` 前缀，如 `v0.0.4`（不是 `0.0.4`）
2. **版本号**：版本号由 `setuptools_scm` 从 git 标签自动获取
3. **Token 安全**：PyPI token 已存储在 GitHub Secrets 中，不会暴露在代码中
4. **发布检查**：工作流会自动检查包的有效性，确保发布成功

## 查看发布状态

发布后可以在以下位置查看：
- GitHub Actions: https://github.com/all-for-freedom/scriptperf/actions
- PyPI: https://pypi.org/project/scriptperf/

