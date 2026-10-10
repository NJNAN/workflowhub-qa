# 后端项目面试准备

参考答案是代码导航，需本人实际演练，不能当成已经具备能力的声明。

## 1. 为何做工单而不是微服务？
原项目已有基础设施证据；PRD用指派、确认关闭和资产关系补业务规则，单进程降低部署成本。

## 2. 表之间的关系和约束？
models.py五类数据加会话；工单关联创建者、可空负责人/资产；唯一工单号和用户+幂等键；FK使不存在引用失败。

## 3. 为什么MySQL？
关联一致性、事务与索引适合工单审计；SQLite便携但锁/计划行为不同，46项MySQL复跑避免只验证SQLite。

## 4. 会话如何撤销？
security.py随机opaque令牌只存SHA256摘要；8小时期限；auth/logout删除当前会话。不用JWT避免另建撤销名单。

## 5. 密码为何不能明文？
scrypt随机盐；verify constant-time比较摘要。auth.py未知用户用预计算dummy，回归验证两类请求各一次KDF。

## 6. 角色与资源权限如何区分？
require_admin约束操作，ticket_for_user约束资源；visible_to同时用于列表/count/stats，不允许详情挡住但统计泄露。

## 7. 状态怎么防止客户端改坏？
schemas extra=forbid，状态有专用transition；services白名单合法pair，指派单独使OPEN进入IN_PROGRESS。

## 8. 并发修改的真实机制？
UPDATE WHERE id和version；rowcount不是1返回409，审计仅赢家写；双线程屏障案例验证1个200和1个409。

## 9. 业务更新成功而审计失败怎么办？
db.py请求同Session commit/rollback；Depends scope=function保证提交在响应之前。故意审计异常证明修改回滚。

## 10. 幂等键如何处理网络重试？
按creator+key唯一；hash载荷相同返原资源200，不同409。两个首次同时插入冲突409，客户端同key再试。前端同表单复用key。

## 11. 如何分页稳定？
created_at再id排序，过滤/count同谓词；页大小1–100；大offset仍慢，可后续游标分页。

## 12. SQL注入与LIKE通配符？
ORM绑定不是拼接SQL；literal_pattern用!转义%/_。测试恶意字符串不会扩大结果，但不是完整渗透结论。

## 13. 索引为什么这样设计？
status/creator/assignee后接时间和id匹配过滤排序；benchmark和MySQL EXPLAIN见报告；不能宣称一个索引覆盖所有OR权限查询。

## 14. MySQL EXPLAIN能证明提速吗？
它描述估计计划；IGNORE/FORCE+ANALYZE控制计划仅说明机制，没有测MySQL延迟，不能说提速几倍。

## 15. 异常码怎么区分？
401未认证/撤销，403角色资源拒绝，404不存在，409业务/唯一/版本，422输入，503数据库异常。main.py不回显密码输入。

## 16. 迁移为何冻结？
Alembic版本描述历史schema，不在迁移运行时create_all最新模型；upgrade/downgrade往返验证，生产降级仍需备份。

## 17. 前端怎样联调？
浏览器同源fetch，令牌内存保存；详情拿version再写；textContent显示数据；无刷新保持登录与复杂SPA依赖。

## 18. 部署与CI的边界？
Compose web+MySQL，迁移先执行，health依赖，非root应用。CI YAML对应本地检查通过，未发布仓库所以远程Actions未验证。
