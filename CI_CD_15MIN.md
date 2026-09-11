# 15 分钟 CI/CD 实操

这个仓库使用 GitHub Actions 把一次 `push` 变成一条真实执行的流水线：

```text
push / PR
    -> Test（安装依赖并运行 pytest）
    -> Build（打包 app.py 为 app.tar.gz）
    -> Deploy demo（下载同一个构建产物、解包、运行并验证）
```

## 0–2 分钟：理解本次失败

原来的工作流运行 `pip install -r requirements.txt`，但仓库当时没有
`requirements.txt`。GitHub 的临时 runner 因而会在依赖安装步骤报
`No such file or directory`，测试尚未开始。

`requirements.txt` 是可复现构建的依赖清单；它让每一台新 runner 安装相同的
测试工具版本。本项目现在固定使用 `pytest==8.3.5`。

## 2–5 分钟：先在本机跑 CI 的核心步骤

在仓库根目录执行：

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest -q
```

预期输出是 `1 passed`。这不是替代云端 CI：本地验证快，而云端 runner 提供
一个干净、与个人电脑无关的复现环境。

## 5–8 分钟：提交并触发真实 GitHub Actions

```sh
git add .github/workflows/ci.yml requirements.txt .gitignore CI_CD_15MIN.md
git commit -m "add CI CD demo pipeline"
git push origin main
```

打开仓库的 **Actions** 页面，点开最新的 **CI-CD demo** 运行。依次观察
`Test`、`Build deployable artifact`、`Deploy to demo environment` 三个 job。

## 8–11 分钟：读懂 CI

CI（持续集成）的目标是在每次改动合入前尽早证明它仍可用。`test` job 从全新的
`ubuntu-latest` 虚拟机开始，检出代码、设置 Python、安装依赖、运行测试。

每个 job 默认互相隔离；`needs: test` 是质量门：测试失败时，构建不会运行。
同样，`needs: build` 保证部署只拿到已经成功构建的版本。

对 `pull_request` 事件，流水线只运行 Test 和 Build。这让 PR 在合并前接受检查，
并避免未合并的代码部署。

## 11–14 分钟：读懂 CD

CD（持续交付/部署）将已验证的构建产物送往环境。本示例的 `build` job 只打包一次
`app.tar.gz`，然后上传为 Actions artifact。部署 job 下载**同一个** artifact，解包
并执行程序。这是关键原则：部署的是已测试的成品，不能在部署阶段重新从源码构建。

本仓库的 `deploy-demo` 是安全的模拟部署：它实际执行打包、传递、解包和发布验证，
但不会连接外部生产服务。它仅在 `push` 到 `main` 时运行；PR 不会触发部署。

在 Actions 运行详情的 Summary 中可以看到被部署的 commit SHA。这个 SHA 是发布可
追溯性的基础：出现问题时可明确知道哪次提交进入了哪个环境。

## 14–15 分钟：体验一次失败保护（可选）

把 `test_app.py` 的期望值临时改错，执行以下命令创建 PR：

```sh
git switch -c codex/try-failing-ci
# 修改 test_app.py，让断言故意失败
git add test_app.py
git commit -m "demonstrate failing CI"
git push -u origin codex/try-failing-ci
```

在 GitHub 创建 Pull Request 后，CI 会红灯，Build 和 Deploy 不会运行。修正断言后
再次 push，检查会变绿；合并 PR 后，main 的 push 才会进入 demo 部署。这就是“先检查、
后构建、再部署”的质量门。

## 从模拟到真实部署

真实部署只替换 `deploy-demo` 内的最后一步，例如调用云厂商 CLI、SSH 或 Kubernetes。
部署凭证必须放在 GitHub **Settings → Secrets and variables → Actions**，以
`${{ secrets.DEPLOY_TOKEN }}` 读取；绝不能提交到仓库。生产环境还应在
**Settings → Environments → production** 配置审批人，形成“CI 自动、生产部署经批准”
的安全门。
