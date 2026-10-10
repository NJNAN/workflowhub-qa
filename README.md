# WorkFlowHub QA

独立接口自动化测试项目，针对真实自研 WorkFlowHub开展质量保障。它通过 HTTP 访问被测系统，不导入业务代码，不冒充企业测试实习。

目标：把 PRD 的权限、状态、边界和异常规则转为回归验收。Python 3.11+、pytest、httpx；角色矩阵、边界值、状态迁移、跨用户访问、幂等与陈旧版本回归。数据库事务和双线程竞争属于业务仓库白盒/集成测试，两部分证据分别统计。

## 本地自动运行
两个仓库放在同一父目录，名为 workflowhub 和 workflowhub-qa。可使用任意位置的业务仓库，通过 WORKFLOWHUB_PATH 指定绝对路径。
```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[dev]' -e '..\workflowhub[test]'
New-Item -ItemType Directory -Path reports -Force
.\.venv\Scripts\python.exe -m pytest --basetemp=reports/tmp-local --junitxml=reports/junit.xml
```
交付共享环境可替换为 `..\.venv\Scripts\python.exe`。fixture 自动创建临时数据库、执行迁移、生成随机演示账号、启动 localhost uvicorn，轮询健康端点，再运行测试；结束关闭测试进程。保留服务日志在临时目录，账号文件不得公开。

## 测试已启动的 MySQL/容器系统
```powershell
$env:QA_BASE_URL='http://127.0.0.1:8012'
$env:QA_ACCOUNTS_FILE=(Resolve-Path '..\workflowhub\reports\compose_accounts.json').Path
.\.venv\Scripts\python.exe -m pytest --basetemp=reports/tmp-compose --junitxml=reports/compose_junit.xml
Remove-Item Env:QA_BASE_URL
Remove-Item Env:QA_ACCOUNTS_FILE
```
仅用于本项目隔离的演示环境；测试会创建账号关联数据、资产与工单。需要四个初始账号 admin/engineer/requester/other，并建议 other 账号保持无工单。不能随意对生产接口运行。

## Postman 与 Apifox
导入 collections/workflowhub.postman_collection.json。变量 base_url、三角色密码、run_id 在本机填写，密码从演示账号文件读取。先运行 admin 登录、创建资产、查询用户；再 requester 登录、创建工单；重新 admin 登录后指派；engineer 登录后记录和解决；requester 登录后关闭/重开。登录脚本更新 token，写接口响应更新 version。状态操作必须按角色切换；该集合为联调素材，未宣称在 Postman/Apifox 客户端执行通过。自动化验收以 pytest 报告为准。

## 质量材料
docs/test_plan.md、test_cases.md、bug_reports.md、test_report.md 给出需求、用例、真实缺陷与注入实验、结果。JUnit 在 reports/。`.github/workflows/ci.yml` 使用 workflow_dispatch 接收已发布业务仓库及固定 commit/tag，避免假设不存在的 GitHub URL；配置已提供，远程运行未验证。

## 限制
当前独立套件验证同步 HTTP 合同，未覆盖跨浏览器自动化、移动端真实设备、安全渗透和长期压力稳定性。浏览器实际操作验收单独记录，不混入自动化用例数。未来可扩展 UI 自动化、数据驱动用例和失败请求脱敏附件。

单独测试外部服务时只需 `python -m venv .venv` 与 `.\.venv\Scripts\python.exe -m pip install -e '.[dev]'`，无需安装或导入业务包；设置QA_BASE_URL和QA_ACCOUNTS_FILE后执行上面的命令。
