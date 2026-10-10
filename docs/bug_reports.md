# 实际缺陷与回归记录
2026-10-10独立工程审查发现以下3个P2；没有宣称发现企业生产Bug。B001含真实失败测试；B002/B003来自代码路径审查。故障注入另列。

## B001 错误登录的用户名时间差
环境：Windows/Python3.12，scrypt。步骤：分别对已存在requester和不存在用户提交错误密码，多次测量。预期都执行一次密码KDF；实际未知用户在请求内hash后verify执行两次。审查12轮中位150.42/298.98ms，调用次数回归实际RED=[1,2]，见reports/regression_red.txt。严重度P2，泄露用户存在信号。
根因：fallback在每次请求重新生成hash。修复：启动时生成随机dummy hash，请求只验证一次（routers/auth.py DUMMY_PASSWORD_HASH）。回归：test_unknown_and_known_username_have_one_password_kdf，[1,1]通过，SQLite47与MySQL46全套通过。该修复减少主要时间差，不承诺网络层完全恒定时间；限流尚未实现。

## B002 新建工单重复点击产生不同幂等键
环境：frontend/app.js。复现路径：网络较慢时同表单双击；旧submit handler每次crypto.randomUUID且按钮未禁用，两个请求可各201。预期同一次表单操作只创建一条。P2，工单重复。
根因：后端虽支持幂等，UI没有复用key。修复：打开对话框生成key，同次提交/失败重试复用；creating防重入，按钮在try/finally里禁用恢复。后端同key重发的黑盒与集成测试通过。UI代码路径复核完成；没有做网络节流双击自动化，不把此项写成UI自动测试通过。载荷改动后的同key重试会409，用户重新打开表单获得新key。

## B003 退出保留页面与筛选
环境：原生页面。复现路径：管理员账号管理页退出，再以Requester登录。原reset只隐藏workspace，accounts-panel仍可见；后端写请求仍403。P2体验/角色展示错误，不是后端越权。
修复：reset恢复tickets选中、其他panel隐藏、page=1、筛选与表单清空、关闭对话框和清除临时集合。浏览器实测Requester从设备页退出再登录，显示服务工单第一页、默认筛选；管理员敏感页同一reset路径已代码审查。未声称做跨浏览器全面验收。

## 注入实验 F001 不计真实Bug
故意monkeypatch审计flush抛异常，验证请求事务回滚且不留业务修改/伪历史。另用真实外键违反验证rollback。双线程竞争是设计验收。它们不是“发现并修复了3个数据库Bug”。Docker第一次构建PyPI元数据截断、沙箱异步阻塞是环境事件，也不计产品缺陷。
