#!/usr/bin/env python3
"""
收钱吧支付 Skills 项目验证测试（分层架构版）

验证内容：
1.  目录结构完整性
2.  顶层文档与架构文档存在
3.  SKILL.md frontmatter 完整性
4.  接口 skill 包含分层定位与双模式生成章节
5.  共享模块 skill 包含所属层次与目标输出说明
6.  API 路径与核心关键词校验
7.  Python 参考代码语法检查
8.  Java 参考代码结构检查
9.  安全边界检查（无沙盒 / 验签不可省略）
10. 前端 skill 边界检查
"""

import os
import re
import py_compile

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_SKILLS_DIR = os.path.join(PROJECT_ROOT, "sqb-api-skills")
WEB_SKILLS_DIR = os.path.join(PROJECT_ROOT, "sqb-web-skills")
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")

INTERFACE_SKILLS = [
    "sqb-activate",
    "sqb-checkin",
    "sqb-pay",
    "sqb-precreate",
    "sqb-query",
    "sqb-refund",
    "sqb-cancel",
    "sqb-notify",
]

SHARED_SKILLS = [
    "sqb-signing",
    "sqb-status-parsing",
    "sqb-polling",
    "sqb-callback-verify",
]

EXPECTED_API_PATHS = {
    "sqb-activate": "/terminal/activate",
    "sqb-checkin": "/terminal/checkin",
    "sqb-pay": "/upay/v2/pay",
    "sqb-precreate": "/upay/v2/precreate",
    "sqb-query": "/upay/v2/query",
    "sqb-refund": "/upay/v2/refund",
    "sqb-cancel": "/upay/v2/cancel",
}


class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def ok(self, msg):
        self.passed += 1
        print(f"  PASS  {msg}")

    def fail(self, msg):
        self.failed += 1
        self.errors.append(msg)
        print(f"  FAIL  {msg}")

    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'=' * 60}")
        print(f"结果: {self.passed}/{total} 通过, {self.failed} 失败")
        if self.errors:
            print("\n失败项:")
            for err in self.errors:
                print(f"  - {err}")
        print(f"{'=' * 60}")
        return self.failed == 0


def read_text(path):
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def skill_md_path(skill_name):
    return os.path.join(API_SKILLS_DIR, skill_name, "SKILL.md")


def test_structure(result):
    print("\n[测试 1] 目录结构完整性")

    for skill in INTERFACE_SKILLS + SHARED_SKILLS:
        skill_dir = os.path.join(API_SKILLS_DIR, skill)
        if os.path.isdir(skill_dir):
            result.ok(f"{skill}/ 目录存在")
        else:
            result.fail(f"{skill}/ 目录不存在")
            continue

        md_path = os.path.join(skill_dir, "SKILL.md")
        if os.path.isfile(md_path):
            result.ok(f"{skill}/SKILL.md 存在")
        else:
            result.fail(f"{skill}/SKILL.md 不存在")

        ref_dir = os.path.join(skill_dir, "reference")
        if os.path.isdir(ref_dir) and os.listdir(ref_dir):
            result.ok(f"{skill}/reference/ 存在且非空")
        else:
            result.fail(f"{skill}/reference/ 缺失或为空")


def test_docs(result):
    print("\n[测试 2] 顶层文档与架构文档")

    required_docs = [
        os.path.join(PROJECT_ROOT, "README.md"),
        os.path.join(DOCS_DIR, "architecture.md"),
        os.path.join(DOCS_DIR, "migration.md"),
        os.path.join(API_SKILLS_DIR, "README.md"),
    ]
    for doc in required_docs:
        if os.path.isfile(doc):
            result.ok(f"{os.path.relpath(doc, PROJECT_ROOT)} 存在")
        else:
            result.fail(f"{os.path.relpath(doc, PROJECT_ROOT)} 不存在")

    readme = read_text(os.path.join(PROJECT_ROOT, "README.md"))
    for phrase in ["完整流程生成", "单独模块生成", "protocol/client", "adapter", "support", "bootstrap"]:
        if phrase in readme:
            result.ok(f"README.md 包含 {phrase}")
        else:
            result.fail(f"README.md 缺少 {phrase}")


def test_frontmatter(result):
    print("\n[测试 3] SKILL.md frontmatter")

    for skill in INTERFACE_SKILLS + SHARED_SKILLS:
        content = read_text(skill_md_path(skill))
        if content.startswith("---\n"):
            result.ok(f"{skill}/SKILL.md 包含 frontmatter")
        else:
            result.fail(f"{skill}/SKILL.md 缺少 frontmatter")
            continue

        for key in ["name:", "description:", "version:", "tags:", "globs:"]:
            if key in content:
                result.ok(f"{skill}/SKILL.md 包含 {key}")
            else:
                result.fail(f"{skill}/SKILL.md 缺少 {key}")


def test_interface_skills(result):
    print("\n[测试 4] 接口 skill 分层与双模式契约")

    required_phrases = [
        "## 分层定位",
        "### 完整流程",
        "### 单独模块",
        "## 完整流程生成",
        "## 单独模块生成",
        "## 生成规则",
    ]

    for skill in INTERFACE_SKILLS:
        content = read_text(skill_md_path(skill))
        for phrase in required_phrases:
            if phrase in content:
                result.ok(f"{skill}/SKILL.md 包含 {phrase}")
            else:
                result.fail(f"{skill}/SKILL.md 缺少 {phrase}")

        if any(layer in content for layer in ["protocol/", "adapter/", "support/", "bootstrap/"]):
            result.ok(f"{skill}/SKILL.md 包含分层输出说明")
        else:
            result.fail(f"{skill}/SKILL.md 缺少分层输出说明")


def test_shared_skills(result):
    print("\n[测试 5] 共享模块 skill 层次与目标输出")

    layer_expectations = {
        "sqb-signing": "protocol/security",
        "sqb-status-parsing": "support/status",
        "sqb-polling": "support/polling",
        "sqb-callback-verify": "protocol/security",
    }

    for skill, layer in layer_expectations.items():
        content = read_text(skill_md_path(skill))
        for phrase in ["## 分层定位", "## 目标输出", "## 生成规则"]:
            if phrase in content:
                result.ok(f"{skill}/SKILL.md 包含 {phrase}")
            else:
                result.fail(f"{skill}/SKILL.md 缺少 {phrase}")

        if layer in content:
            result.ok(f"{skill}/SKILL.md 标注所属层 {layer}")
        else:
            result.fail(f"{skill}/SKILL.md 缺少层次标注 {layer}")


def test_api_paths(result):
    print("\n[测试 6] API 路径与核心关键词")

    for skill, path in EXPECTED_API_PATHS.items():
        content = read_text(skill_md_path(skill))
        if path in content:
            result.ok(f"{skill}/SKILL.md 包含 {path}")
        else:
            result.fail(f"{skill}/SKILL.md 缺少 {path}")

    refund = read_text(skill_md_path("sqb-refund"))
    for phrase in ["refund_request_no", "refund_amount", "部分退款"]:
        if phrase in refund:
            result.ok(f"sqb-refund/SKILL.md 包含 {phrase}")
        else:
            result.fail(f"sqb-refund/SKILL.md 缺少 {phrase}")

    pay = read_text(skill_md_path("sqb-pay"))
    for phrase in ["client_sn", "dynamic_id", "total_amount"]:
        if phrase in pay:
            result.ok(f"sqb-pay/SKILL.md 包含 {phrase}")
        else:
            result.fail(f"sqb-pay/SKILL.md 缺少 {phrase}")


def test_python_syntax(result):
    print("\n[测试 7] Python 参考代码语法")

    dirs = [os.path.join(API_SKILLS_DIR, skill, "reference") for skill in INTERFACE_SKILLS + SHARED_SKILLS]
    dirs.append(os.path.join(API_SKILLS_DIR, "shared-reference"))

    for ref_dir in dirs:
        if not os.path.isdir(ref_dir):
            continue
        for fname in os.listdir(ref_dir):
            if not fname.endswith(".py"):
                continue
            path = os.path.join(ref_dir, fname)
            try:
                py_compile.compile(path, doraise=True)
                result.ok(f"{os.path.relpath(path, PROJECT_ROOT)} 语法正确")
            except py_compile.PyCompileError as exc:
                result.fail(f"{os.path.relpath(path, PROJECT_ROOT)} 语法错误: {exc}")


def test_java_shape(result):
    print("\n[测试 8] Java 参考代码结构")

    dirs = [os.path.join(API_SKILLS_DIR, skill, "reference") for skill in INTERFACE_SKILLS + SHARED_SKILLS]
    dirs.append(os.path.join(API_SKILLS_DIR, "shared-reference"))

    for ref_dir in dirs:
        if not os.path.isdir(ref_dir):
            continue
        for fname in os.listdir(ref_dir):
            if not fname.endswith(".java"):
                continue
            path = os.path.join(ref_dir, fname)
            content = read_text(path)
            has_class = bool(re.search(r"\bclass\s+\w+", content))
            braces_ok = content.count("{") > 0 and content.count("{") == content.count("}")
            if has_class and braces_ok:
                result.ok(f"{os.path.relpath(path, PROJECT_ROOT)} 结构正确")
            else:
                result.fail(f"{os.path.relpath(path, PROJECT_ROOT)} 结构异常")


def test_security_boundaries(result):
    print("\n[测试 9] 安全边界检查")

    for skill in ["sqb-pay", "sqb-precreate", "sqb-query", "sqb-refund", "sqb-cancel"]:
        content = read_text(skill_md_path(skill))
        if "无沙盒环境警告" in content or "无沙盒环境" in content:
            result.ok(f"{skill}/SKILL.md 包含无沙盒提醒")
        else:
            result.fail(f"{skill}/SKILL.md 缺少无沙盒提醒")

    notify = read_text(skill_md_path("sqb-notify"))
    for phrase in ["RSA", "SHA256WithRSA", "幂等", "success"]:
        if phrase in notify:
            result.ok(f"sqb-notify/SKILL.md 包含 {phrase}")
        else:
            result.fail(f"sqb-notify/SKILL.md 缺少 {phrase}")


def test_frontend_boundary(result):
    print("\n[测试 10] 前端 skill 边界")

    path = os.path.join(WEB_SKILLS_DIR, "sqb-cashier-ui", "SKILL.md")
    if not os.path.isfile(path):
        result.fail("sqb-web-skills/sqb-cashier-ui/SKILL.md 不存在")
        return

    content = read_text(path)
    for phrase in ["后端", "facade", "不应该直接感知", "terminal_key", "签名"]:
        if phrase in content:
            result.ok(f"sqb-cashier-ui/SKILL.md 包含 {phrase}")
        else:
            result.fail(f"sqb-cashier-ui/SKILL.md 缺少 {phrase}")


def main():
    print("=" * 60)
    print("收钱吧支付 Skills 项目 —— 验证测试 v4")
    print("=" * 60)

    result = TestResult()
    test_structure(result)
    test_docs(result)
    test_frontmatter(result)
    test_interface_skills(result)
    test_shared_skills(result)
    test_api_paths(result)
    test_python_syntax(result)
    test_java_shape(result)
    test_security_boundaries(result)
    test_frontend_boundary(result)

    return 0 if result.summary() else 1


if __name__ == "__main__":
    raise SystemExit(main())
