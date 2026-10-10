import json
from pathlib import Path


def request(name, method, path, body=None, tests=None):
    item = {
        "name": name,
        "request": {
            "method": method,
            "header": [{"key": "Authorization", "value": "Bearer {{token}}"}],
            "url": "{{base_url}}/api" + path,
        },
    }
    if body is not None:
        item["request"]["header"].append({"key": "Content-Type", "value": "application/json"})
        item["request"]["body"] = {
            "mode": "raw",
            "raw": json.dumps(body, ensure_ascii=False),
            "options": {"raw": {"language": "json"}},
        }
    if tests:
        item["event"] = [{"listen": "test", "script": {"type": "text/javascript", "exec": tests}}]
    return item


items = []
for name in ["admin", "requester", "engineer"]:
    group = [
        request(
            "登录 " + name,
            "POST",
            "/auth/login",
            {"username": name, "password": "{{" + name + "_password}}"},
            [
                'pm.test("登录成功",()=>pm.response.to.have.status(200));',
                'if(pm.response.code===200)pm.collectionVariables.set("token",pm.response.json().access_token);',
            ],
        )
    ]
    if name == "admin":
        group += [
            request(
                "创建资产",
                "POST",
                "/assets",
                {"code": "POSTMAN-{{run_id}}", "name": "演示电脑"},
                [
                    'if(pm.response.code===201)pm.collectionVariables.set("asset_id",pm.response.json().id);'
                ],
            ),
            request(
                "查询用户并记录工程师 ID",
                "GET",
                "/users",
                tests=[
                    'const u=pm.response.json().find(u=>u.username==="engineer"); if(u)pm.collectionVariables.set("engineer_id",u.id);'
                ],
            ),
            request("资产列表", "GET", "/assets"),
        ]
    if name == "requester":
        group += [
            request(
                "创建工单",
                "POST",
                "/tickets",
                {
                    "title": "办公设备无法连接",
                    "description": "检查网络连接",
                    "asset_id": "{{asset_id}}",
                },
                [
                    'if(pm.response.code===201){pm.collectionVariables.set("ticket_id",pm.response.json().id);pm.collectionVariables.set("version",pm.response.json().version);}'
                ],
            ),
            request("工单列表", "GET", "/tickets?status=OPEN&page=1&size=20"),
            request("本人信息", "GET", "/auth/me"),
        ]
        # JSON number placeholders must remain raw, unquoted.
        group[1]["request"]["body"]["raw"] = group[1]["request"]["body"]["raw"].replace(
            '"{{asset_id}}"', "{{asset_id}}"
        )
    if name == "engineer":
        group += [
            request("处理人可见工单", "GET", "/tickets"),
            request("查看工单历史", "GET", "/tickets/{{ticket_id}}/history"),
        ]
    items.append({"name": name + " 操作", "item": group})
items.append(
    {
        "name": "状态流转（按角色切换 token 后操作）",
        "item": [
            request(
                "管理员指派",
                "POST",
                "/tickets/{{ticket_id}}/assign",
                {"version": "{{version}}", "assignee_id": "{{engineer_id}}"},
            ),
            request(
                "工程师处理记录",
                "POST",
                "/tickets/{{ticket_id}}/notes",
                {"version": "{{version}}", "text": "已检查网络"},
            ),
            request(
                "工程师解决",
                "POST",
                "/tickets/{{ticket_id}}/transition",
                {"version": "{{version}}", "target": "RESOLVED"},
            ),
            request(
                "创建者关闭",
                "POST",
                "/tickets/{{ticket_id}}/transition",
                {"version": "{{version}}", "target": "CLOSED"},
            ),
            request(
                "创建者重开",
                "POST",
                "/tickets/{{ticket_id}}/transition",
                {"version": "{{version}}", "target": "OPEN"},
            ),
            request("退出登录", "POST", "/auth/logout"),
        ],
    }
)
for item in items[-1]["item"]:
    if "body" in item["request"]:
        item["request"]["body"]["raw"] = (
            item["request"]["body"]["raw"]
            .replace('"{{version}}"', "{{version}}")
            .replace('"{{engineer_id}}"', "{{engineer_id}}")
        )
        item["event"] = [
            {
                "listen": "test",
                "script": {
                    "type": "text/javascript",
                    "exec": [
                        'if(pm.response.code<300&&pm.response.code!==204)pm.collectionVariables.set("version",pm.response.json().version);'
                    ],
                },
            }
        ]
variables = [
    {"key": k, "value": v}
    for k, v in {
        "base_url": "http://127.0.0.1:8011",
        "token": "",
        "admin_password": "",
        "requester_password": "",
        "engineer_password": "",
        "run_id": "manual-001",
        "asset_id": "",
        "ticket_id": "",
        "engineer_id": "",
        "version": "1",
    }.items()
]
collection = {
    "info": {
        "name": "WorkFlowHub API 操作与回归",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        "description": "导入 Postman/Apifox；密码只在本机填写。状态流转需按 README 切换角色，不能整集合直接无差别运行。",
    },
    "variable": variables,
    "item": items,
}
path = Path("collections/workflowhub.postman_collection.json")
path.parent.mkdir(exist_ok=True)
path.write_text(json.dumps(collection, ensure_ascii=False, indent=2), encoding="utf-8")
print("Exported", path)
