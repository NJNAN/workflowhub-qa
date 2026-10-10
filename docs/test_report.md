# 实际工程验证报告
日期2026-10-10。每个结果对应已执行的本地文件。测试是产物验收，不能推出候选人已独立掌握所有代码。

|层次|结果|原始证据|
|---|---|---|
|业务SQLite ASGI/单元/数据库|47项，失败/错误0，JUnit耗时17.52秒|workflowhub/reports/junit.xml|
|真实MySQL8.4.11专项|46项，失败/错误0，JUnit耗时51.40秒|mysql_junit.xml、mysql_verify.log|
|独立真实HTTP/临时SQLite服务|17项，失败/错误0，JUnit耗时6.75秒|workflowhub-qa/reports/junit.xml|
|独立Compose+MySQL服务|17项，失败/错误0，JUnit耗时1.46秒|workflowhub-qa/reports/compose_junit.xml|
|Docker启动|以docker_verification.txt为准|workflowhub/reports/docker_verification.txt|
|静态检查|ruff check通过；format检查收尾单独记录|reports/final_checks.txt|
|远程GitHub Actions|业务与独立QA均通过|[业务CI](https://github.com/NJNAN/workflowhub/actions/runs/38063407527)、[QA CI](https://github.com/NJNAN/workflowhub-qa/actions/runs/38063437949)；固定提交见source_versions.md|
|Postman/Apifox|有可导入集合，客户端未执行|QA collections/|

coverage统计397/413行，96.13%，仅用于定位遗漏，没有用覆盖率包装能力。47与46是同一套大部分案例在不同数据库复跑，不能相加为93个独立用例。浏览器中文创建/详情、页签重置为手动操作；没有计入17项。

## 性能实验与SQL
环境：Windows-11-10.0.26200-SP0，Python3.12.14，Intel64 Family 6 Model 186 Stepping 2, GenuineIntel，逻辑CPU16。单uvicorn worker、本机TCP、SQLite WAL。HTTP创建100条语料，测量时可见100条，预热10次，200请求、并发4，P50=16.09ms，P95=24.19ms，吞吐=236.00req/s，错误率=0.0%，总计0.847s。包含查询/count/授权/响应；不等于外网负载或生产容量。原始每请求延迟和状态在benchmark.json；此结果不写进简历。

SQLite独立SQL实验10000条、相同参数/20次预热/200样本。SQL：`SELECT id, title FROM bench_tickets WHERE status = ? ORDER BY created_at DESC, id DESC LIMIT 20`。未索引计划SCAN与临时排序；复合索引status,created_at,id后为SEARCH且排序沿索引。前/后P50=0.3966/0.0212ms，P95=0.5588/0.0288ms。原始样本包含在JSON。缓存、先后顺序和极短时延限制很强，不推断MySQL性能提升。

真实MySQL在专用测试库插入10000条合成数据（另有1条测试工单），ANALYZE后保存JSON EXPLAIN；相同查询以IGNORE/FORCE INDEX控制是否使用ix_ticket_status_time，前者ALL+filesort，后者ref+backward index scan且无filesort。强制索引只是受控说明，不能证明优化器默认总选此索引；没有测MySQL前后延迟，也不宣称其提速倍数。见mysql_explain.json。实际工单授权谓词可能包含creator/assignee，不用该单条件实验冒充全部业务查询。

## 限制与结论
权限、状态、事务、迁移与并发关键场景通过。3个P2详见bug_reports；UI网络节流双击尚无自动化回归。资产UI固定加载100条，多资产分页体验后续补充；未做认证限流、密码找回、公网TLS、安全渗透、跨浏览器和长时压力。依赖版本范围并非完整跨平台锁文件。本项目足以供本机学习和代码审查，个人面试讲解与生产交付仍各需独立验收。
