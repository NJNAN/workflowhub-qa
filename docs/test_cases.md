# 需求与测试用例
以下是设计场景组，不等于pytest参数展开数量。实际执行条目以JUnit为准。所有业务自动场景已在SQLite执行；MySQL套件46项不含test_boot，迁移往返仍使用自己的临时SQLite文件。此差异不隐藏为“所有47项均跑在MySQL”。

|编号|需求|数据/方法|预期|代码函数（tests下）|执行|
|---|---|---|---|---|---|
|TC01|AUTH-01|正确/错误密码、不存在用户；退出/过期|200/401；撤销后拒绝|test_login_logout_revoke; test_bad_credentials_and_expired_session|通过|
|TC02|SEC-01|已知/未知用户名错误登录|各1次scrypt；响应相同401|test_unknown_and_known_username_have_one_password_kdf|通过|
|TC03|ACL-01|无令牌访问5受保护接口|全部401|test_unauthenticated_endpoints|通过|
|TC04|AUTH-01|管理员建账号；普通用户写；重名|201/403/409且不返回hash|test_admin_accounts_unique_and_role_protected|通过|
|TC05|TKT-01/AUDIT-01|创建关联资产工单|201、创建者正确、created历史|test_ticket_creation_and_audit|通过|
|TC06|TKT-01/SEC-01|标题空、121；优先级越界；额外字段|422且不接受注入状态|test_invalid_creation|通过|
|TC07|ACL-01|另一申请人详情/编辑/历史/统计|403；列表和统计无资源|test_resource_and_statistics_do_not_leak|通过|
|TC08|FLOW-01/02|指派→记录→解决→关闭→重开|200/201，版本递增，重开清空指派|test_complete_state_machine_and_stale_version|通过|
|TC09|FLOW-02|4种状态共16对迁移|4对允许，12对409；指派走单独入口|test_state_matrix|通过|
|TC10|EDIT-01|两个线程读取同一版本再更新|恰1个200、1个409、1条新审计|test_two_concurrent_writers_one_version|通过|
|TC11|TKT-01|同用户同幂等键重发；异载荷|201后200同id；异载荷409|test_idempotency_replay_and_payload_conflict|通过|
|TC12|AST-01|普通用户登记；重码；退役关联|403/409；禁止退役资产新工单|test_assets_unique_retired_and_permissions|通过|
|TC13|TKT-02|组合筛选、排序、页边界、%和SQL字符串|稳定无重复；按字面检索；未扩大查询|test_combined_filters_stable_pagination_and_literal_search|通过|
|TC14|AUDIT-01|注入审计flush异常|请求失败，业务修改回滚，无伪历史|test_audit_failure_rolls_back_business|通过|
|TC15|OPS-01|upgrade/downgrade/upgrade临时库|表创建、删除、重建|test_migration_roundtrip|通过|
|TC16|SEC-01|盐不同、错误hash、输入含密码|hash不同；错误拒绝；422不回显密码|test_password_salt_and_invalid_hash; test_validation_does_not_echo_password|通过|
|TC17|EDIT-01/ACL-01|空值编辑、非管理员指派|422/403|test_null_edit_and_assign_by_non_admin|通过|
|TC18|DB|不存在外键记录与回滚|IntegrityError；rollback可继续|test_foreign_key_constraint_and_rollback|通过|

独立黑盒：test_contract.py共17项，包含5个未登录路径、3个资产角色、4个非法创建边界，以及健康/网页、完整流程、跨用户、重复/陈旧、退出/OpenAPI。实际TCP场景通过，ASGI同合同不是重复加总的新覆盖。

浏览器场景：新建中文工单并关联IT001、查看与编辑详情；设备页退出再登录回到工单第一页和默认筛选已操作核验。管理员表单重置及重复点击防护见bug_reports；以相应证据程度标记，不把代码审查当作全套UI自动化通过。
