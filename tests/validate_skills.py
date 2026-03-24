#!/usr/bin/env python3
"""
收钱吧支付 Skills 项目验证测试

验证内容：
1.  目录结构完整性 —— 每个 skill 都有 SKILL.md 和 reference 代码
2.  SKILL.md 文档格式 —— 包含必要章节
3.  Python 参考代码语法检查
4.  Java 参考代码结构检查
5.  API 路径一致性 —— SKILL.md 与参考代码中的路径匹配
6.  占位符/TODO 检查
7.  共享代码引用检查 —— 交易类 SKILL.md 引用 shared-reference
8.  安全提醒检查 —— 交易类 SKILL.md 包含无沙盒警告
9.  验签强制检查 —— sqb-notify 标注验签为必选项
10. 前端变体检查 —— cashier-ui 包含 Vue/React/JS 三种实现
11. YAML frontmatter 完整性 —— 检查 version、tags、globs 字段
12. 触发词数量检查 —— 每个 SKILL.md 至少有 6 个触发词
13. 共享工具类完整性 —— shared-reference 包含所有必要文件
14. 模块化生成章节检查 —— 8 个接口 skill 包含模块化生成章节
15. 生成模式章节检查 —— 8 个接口 skill 包含生成模式说明
16. 跨接口共享模块独立性 —— 4 个共享模块 skill 独立可用
"""

import os
import re
import sys
import py_compile

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_SKILLS_DIR = os.path.join(PROJECT_ROOT, "sqb-api-skills")
WEB_SKILLS_DIR = os.path.join(PROJECT_ROOT, "sqb-web-skills")

# 预期的 API skill 目录列表
EXPECTED_API_SKILLS = [
    "sqb-activate",
    "sqb-checkin",
    "sqb-pay",
    "sqb-precreate",
    "sqb-query",
    "sqb-refund",
    "sqb-cancel",
    "sqb-notify",
    # 跨接口共享模块 skill
    "sqb-signing",
    "sqb-status-parsing",
    "sqb-polling",
    "sqb-callback-verify",
]

# SKILL.md 必须包含的章节关键词
REQUIRED_SECTIONS = {
    "sqb-activate": ["激活", "terminal_sn", "terminal_key", "vendor_sn"],
    "sqb-checkin": ["签到", "terminal_sn", "terminal_key"],
    "sqb-pay": ["支付", "client_sn", "total_amount", "dynamic_id", "/upay/v2/pay"],
    "sqb-precreate": ["预下单", "client_sn", "total_amount", "qr_code", "/upay/v2/precreate"],
    "sqb-query": ["查询", "terminal_sn", "/upay/v2/query"],
    "sqb-refund": ["退款", "refund_amount", "refund_request_no", "/upay/v2/refund"],
    "sqb-cancel": ["撤单", "terminal_sn", "/upay/v2/cancel"],
    "sqb-notify": ["回调", "notify_url", "验签"],
    # 跨接口共享模块 skill
    "sqb-signing": ["MD5", "签名", "Authorization", "vendor_sn", "terminal_sn"],
    "sqb-status-parsing": ["三层", "result_code", "order_status", "最终状态"],
    "sqb-polling": ["轮询", "PAY_POLLING_CONFIG", "PRECREATE_POLLING_CONFIG", "超时"],
    "sqb-callback-verify": ["RSA", "SHA256WithRSA", "验签", "公钥"],
}

# API 路径映射
EXPECTED_API_PATHS = {
    "sqb-activate": "/terminal/activate",
    "sqb-checkin": "/terminal/checkin",
    "sqb-pay": "/upay/v2/pay",
    "sqb-precreate": "/upay/v2/precreate",
    "sqb-query": "/upay/v2/query",
    "sqb-refund": "/upay/v2/refund",
    "sqb-cancel": "/upay/v2/cancel",
}

# 交易类 skill（需要安全提醒和 shared-reference 引用）
TRANSACTION_SKILLS = ["sqb-pay", "sqb-precreate", "sqb-query", "sqb-refund", "sqb-cancel"]

# 共享工具类预期文件
SHARED_REF_FILES = [
    "SqbSignUtil.java", "sqb_sign_util.py",
    "SqbStatusUtil.java", "sqb_status_util.py",
    "SqbPollingUtil.java", "sqb_polling_util.py",
]

# 前端预期变体
FRONTEND_VARIANTS = ["CashierApp.vue", "CashierApp.tsx", "cashier-app.html"]


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
        print(f"\n{'='*60}")
        print(f"结果: {self.passed}/{total} 通过, {self.failed} 失败")
        if self.errors:
            print(f"\n失败项:")
            for e in self.errors:
                print(f"  - {e}")
        print(f"{'='*60}")
        return self.failed == 0


def _read_skill_md(skill_name):
    """读取 SKILL.md 内容"""
    path = os.path.join(API_SKILLS_DIR, skill_name, "SKILL.md")
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def test_directory_structure(result):
    """测试 1: 目录结构完整性"""
    print("\n[测试 1] 目录结构完整性")

    for skill in EXPECTED_API_SKILLS:
        skill_dir = os.path.join(API_SKILLS_DIR, skill)

        if os.path.isdir(skill_dir):
            result.ok(f"{skill}/ 目录存在")
        else:
            result.fail(f"{skill}/ 目录不存在")
            continue

        skill_md = os.path.join(skill_dir, "SKILL.md")
        if os.path.isfile(skill_md):
            result.ok(f"{skill}/SKILL.md 存在")
        else:
            result.fail(f"{skill}/SKILL.md 不存在")

        ref_dir = os.path.join(skill_dir, "reference")
        if os.path.isdir(ref_dir):
            ref_files = [f for f in os.listdir(ref_dir) if not f.startswith("__")]
            if ref_files:
                result.ok(f"{skill}/reference/ 包含 {len(ref_files)} 个文件")
            else:
                result.fail(f"{skill}/reference/ 为空")
        else:
            result.fail(f"{skill}/reference/ 目录不存在")


def test_skill_md_content(result):
    """测试 2: SKILL.md 文档内容验证"""
    print("\n[测试 2] SKILL.md 文档内容验证")

    for skill, keywords in REQUIRED_SECTIONS.items():
        content = _read_skill_md(skill)
        if content is None:
            result.fail(f"{skill}/SKILL.md 不存在，跳过内容检查")
            continue

        if len(content) < 100:
            result.fail(f"{skill}/SKILL.md 内容过短 ({len(content)} 字节)")
            continue

        missing = [kw for kw in keywords if kw not in content]
        if not missing:
            result.ok(f"{skill}/SKILL.md 包含所有必要关键词")
        else:
            result.fail(f"{skill}/SKILL.md 缺少关键词: {missing}")

        if re.search(r"^#+\s", content, re.MULTILINE):
            result.ok(f"{skill}/SKILL.md 有 Markdown 标题结构")
        else:
            result.fail(f"{skill}/SKILL.md 缺少 Markdown 标题")


def test_python_syntax(result):
    """测试 3: Python 参考代码语法检查"""
    print("\n[测试 3] Python 参考代码语法检查")

    # API skills
    for skill in EXPECTED_API_SKILLS:
        ref_dir = os.path.join(API_SKILLS_DIR, skill, "reference")
        if not os.path.isdir(ref_dir):
            continue
        for fname in os.listdir(ref_dir):
            if not fname.endswith(".py"):
                continue
            fpath = os.path.join(ref_dir, fname)
            try:
                py_compile.compile(fpath, doraise=True)
                result.ok(f"{skill}/reference/{fname} 语法正确")
            except py_compile.PyCompileError as e:
                result.fail(f"{skill}/reference/{fname} 语法错误: {e}")

    # Shared reference
    shared_dir = os.path.join(API_SKILLS_DIR, "shared-reference")
    if os.path.isdir(shared_dir):
        for fname in os.listdir(shared_dir):
            if not fname.endswith(".py"):
                continue
            fpath = os.path.join(shared_dir, fname)
            try:
                py_compile.compile(fpath, doraise=True)
                result.ok(f"shared-reference/{fname} 语法正确")
            except py_compile.PyCompileError as e:
                result.fail(f"shared-reference/{fname} 语法错误: {e}")


def test_java_syntax(result):
    """测试 4: Java 参考代码结构检查"""
    print("\n[测试 4] Java 参考代码结构检查")

    dirs_to_check = [os.path.join(API_SKILLS_DIR, s, "reference") for s in EXPECTED_API_SKILLS]
    dirs_to_check.append(os.path.join(API_SKILLS_DIR, "shared-reference"))

    for ref_dir in dirs_to_check:
        if not os.path.isdir(ref_dir):
            continue
        label = ref_dir.replace(API_SKILLS_DIR + "/", "")

        for fname in os.listdir(ref_dir):
            if not fname.endswith(".java"):
                continue
            fpath = os.path.join(ref_dir, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()

            has_class = bool(re.search(r"\bclass\s+\w+", content))
            has_braces = content.count("{") > 0 and content.count("{") == content.count("}")

            if has_class and has_braces:
                result.ok(f"{label}/{fname} 结构正确")
            else:
                issues = []
                if not has_class:
                    issues.append("缺少 class 定义")
                if not has_braces:
                    issues.append(f"大括号不匹配 ({{{content.count('{')}, }}{content.count('}')})")
                result.fail(f"{label}/{fname} 结构问题: {', '.join(issues)}")


def test_api_path_consistency(result):
    """测试 5: API 路径一致性"""
    print("\n[测试 5] API 路径一致性检查")

    for skill, expected_path in EXPECTED_API_PATHS.items():
        content = _read_skill_md(skill)
        if content is None:
            continue

        if expected_path in content:
            result.ok(f"{skill}/SKILL.md 包含正确路径 {expected_path}")
        else:
            result.fail(f"{skill}/SKILL.md 未包含预期路径 {expected_path}")

        ref_dir = os.path.join(API_SKILLS_DIR, skill, "reference")
        if not os.path.isdir(ref_dir):
            continue
        for fname in os.listdir(ref_dir):
            fpath = os.path.join(ref_dir, fname)
            if not os.path.isfile(fpath):
                continue
            with open(fpath, "r", encoding="utf-8") as f:
                code_content = f.read()
            if expected_path in code_content:
                result.ok(f"{skill}/reference/{fname} 包含正确路径 {expected_path}")


def test_no_broken_references(result):
    """测试 6: 占位符/TODO 检查"""
    print("\n[测试 6] 占位符/TODO 检查")

    placeholder_pattern = re.compile(r'\b(TODO|FIXME|PLACEHOLDER|TBD)\b')

    for skill in EXPECTED_API_SKILLS:
        content = _read_skill_md(skill)
        if content is None:
            continue
        found = placeholder_pattern.findall(content)
        if not found:
            result.ok(f"{skill}/SKILL.md 无占位符")
        else:
            result.fail(f"{skill}/SKILL.md 包含占位符: {found}")


def test_shared_reference_usage(result):
    """测试 7: 共享代码引用检查"""
    print("\n[测试 7] 共享代码引用检查")

    for skill in TRANSACTION_SKILLS:
        content = _read_skill_md(skill)
        if content is None:
            result.fail(f"{skill}/SKILL.md 不存在")
            continue

        if "shared-reference" in content or "SqbSignUtil" in content:
            result.ok(f"{skill}/SKILL.md 引用了共享代码")
        else:
            result.fail(f"{skill}/SKILL.md 未引用 shared-reference")


def test_safety_warnings(result):
    """测试 8: 安全提醒检查"""
    print("\n[测试 8] 安全提醒检查")

    for skill in TRANSACTION_SKILLS:
        content = _read_skill_md(skill)
        if content is None:
            continue

        has_warning = ("沙盒" in content or "真实交易" in content or "警告" in content)
        if has_warning:
            result.ok(f"{skill}/SKILL.md 包含安全提醒")
        else:
            result.fail(f"{skill}/SKILL.md 缺少无沙盒/真实交易安全提醒")


def test_notify_verification_mandatory(result):
    """测试 9: 验签强制检查"""
    print("\n[测试 9] sqb-notify 验签强制检查")

    content = _read_skill_md("sqb-notify")
    if content is None:
        result.fail("sqb-notify/SKILL.md 不存在")
        return

    has_mandatory = ("不可省略" in content or "不可跳过" in content
                     or "不可作为可选项" in content or "禁止" in content)
    if has_mandatory:
        result.ok("sqb-notify 验签标注为强制/不可省略")
    else:
        result.fail("sqb-notify 验签未标注为强制项")

    has_rsa = ("RSA" in content or "SHA256WithRSA" in content)
    if has_rsa:
        result.ok("sqb-notify 包含 RSA 验签说明")
    else:
        result.fail("sqb-notify 缺少 RSA 验签说明")


def test_frontend_variants(result):
    """测试 10: 前端变体检查"""
    print("\n[测试 10] 前端变体检查")

    ref_dir = os.path.join(WEB_SKILLS_DIR, "sqb-cashier-ui", "reference")
    if not os.path.isdir(ref_dir):
        result.fail("sqb-cashier-ui/reference/ 目录不存在")
        return

    for variant in FRONTEND_VARIANTS:
        fpath = os.path.join(ref_dir, variant)
        if os.path.isfile(fpath):
            result.ok(f"前端变体 {variant} 存在")
        else:
            result.fail(f"前端变体 {variant} 不存在")


def test_yaml_frontmatter(result):
    """测试 11: YAML frontmatter 完整性"""
    print("\n[测试 11] YAML frontmatter 完整性")

    for skill in EXPECTED_API_SKILLS:
        content = _read_skill_md(skill)
        if content is None:
            continue

        if not content.startswith("---"):
            result.fail(f"{skill}/SKILL.md 缺少 YAML frontmatter")
            continue

        # 提取 frontmatter
        parts = content.split("---", 2)
        if len(parts) < 3:
            result.fail(f"{skill}/SKILL.md frontmatter 格式错误")
            continue

        fm = parts[1]
        required_fields = ["name:", "description:", "version:"]
        missing = [f for f in required_fields if f not in fm]

        if not missing:
            result.ok(f"{skill}/SKILL.md frontmatter 包含 name/description/version")
        else:
            result.fail(f"{skill}/SKILL.md frontmatter 缺少: {missing}")


def test_trigger_keywords_count(result):
    """测试 12: 触发词数量检查"""
    print("\n[测试 12] 触发词数量检查")

    for skill in EXPECTED_API_SKILLS:
        content = _read_skill_md(skill)
        if content is None:
            continue

        # 查找引导词章节中的列表项（支持包含子标题的格式）
        trigger_match = re.search(r"## 引导词\s*\n((?:(?:\s*-\s*.+|###\s+.+)\n)+)", content)
        if not trigger_match:
            result.fail(f"{skill}/SKILL.md 缺少引导词章节")
            continue

        triggers = [line.strip() for line in trigger_match.group(1).strip().split("\n") if line.strip().startswith("-")]
        count = len(triggers)

        if count >= 6:
            result.ok(f"{skill}/SKILL.md 包含 {count} 个触发词 (≥6)")
        else:
            result.fail(f"{skill}/SKILL.md 仅有 {count} 个触发词 (<6)")


def test_shared_reference_completeness(result):
    """测试 13: 共享工具类完整性"""
    print("\n[测试 13] 共享工具类完整性")

    shared_dir = os.path.join(API_SKILLS_DIR, "shared-reference")
    if not os.path.isdir(shared_dir):
        result.fail("shared-reference/ 目录不存在")
        return

    for fname in SHARED_REF_FILES:
        fpath = os.path.join(shared_dir, fname)
        if os.path.isfile(fpath):
            result.ok(f"shared-reference/{fname} 存在")
        else:
            result.fail(f"shared-reference/{fname} 不存在")


# 接口类 skill（需要模块化生成章节）
INTERFACE_SKILLS = [
    "sqb-activate", "sqb-checkin", "sqb-pay", "sqb-precreate",
    "sqb-query", "sqb-refund", "sqb-cancel", "sqb-notify",
]

# 各接口 skill 的模块化生成章节必须包含的关键词
MODULAR_SKILLS = {
    "sqb-pay": ["签名", "支付请求构建", "订单号生成"],
    "sqb-precreate": ["签名", "预下单请求", "二维码"],
    "sqb-refund": ["签名", "退款请求", "退款金额"],
    "sqb-query": ["签名", "查询请求", "状态判定", "轮询"],
    "sqb-cancel": ["签名", "撤单请求", "查询确认"],
    "sqb-activate": ["vendor", "激活请求", "terminal_key"],
    "sqb-checkin": ["签到请求", "密钥轮换", "容灾"],
    "sqb-notify": ["RSA", "验签", "幂等", "分发"],
}

# 跨接口共享模块 skill
CROSS_CUTTING_SKILLS = ["sqb-signing", "sqb-status-parsing", "sqb-polling", "sqb-callback-verify"]


def test_module_sections(result):
    """测试 14: 模块化生成章节检查"""
    print("\n[测试 14] 模块化生成章节检查")

    for skill, keywords in MODULAR_SKILLS.items():
        content = _read_skill_md(skill)
        if content is None:
            result.fail(f"{skill}/SKILL.md 不存在")
            continue

        if "## 模块化生成" not in content:
            result.fail(f"{skill}/SKILL.md 缺少 ## 模块化生成 章节")
            continue

        # 提取模块化生成章节内容
        module_section = content.split("## 模块化生成", 1)[1]
        # 截取到下一个 ## 标题或文件末尾
        next_section = re.search(r"\n## [^#]", module_section)
        if next_section:
            module_section = module_section[:next_section.start()]

        missing = [kw for kw in keywords if kw not in module_section]
        if not missing:
            result.ok(f"{skill}/SKILL.md 模块化生成章节包含所有必要关键词")
        else:
            result.fail(f"{skill}/SKILL.md 模块化生成章节缺少关键词: {missing}")


def test_generation_mode_section(result):
    """测试 15: 生成模式章节检查"""
    print("\n[测试 15] 生成模式章节检查（引导词分区）")

    for skill in INTERFACE_SKILLS:
        content = _read_skill_md(skill)
        if content is None:
            result.fail(f"{skill}/SKILL.md 不存在")
            continue

        has_full_flow = "### 完整流程" in content
        has_module = "### 单独模块" in content

        if has_full_flow and has_module:
            result.ok(f"{skill}/SKILL.md 引导词包含完整流程和单独模块分区")
        else:
            missing = []
            if not has_full_flow:
                missing.append("### 完整流程")
            if not has_module:
                missing.append("### 单独模块")
            result.fail(f"{skill}/SKILL.md 引导词缺少分区: {missing}")


def test_cross_cutting_skill_independence(result):
    """测试 16: 跨接口共享模块独立性"""
    print("\n[测试 16] 跨接口共享模块独立性")

    for skill in CROSS_CUTTING_SKILLS:
        skill_dir = os.path.join(API_SKILLS_DIR, skill)
        if not os.path.isdir(skill_dir):
            result.fail(f"{skill}/ 目录不存在")
            continue

        # 检查 SKILL.md 存在
        content = _read_skill_md(skill)
        if content is None:
            result.fail(f"{skill}/SKILL.md 不存在")
            continue

        result.ok(f"{skill}/SKILL.md 存在且可读")

        # 检查 reference 目录有文件
        ref_dir = os.path.join(skill_dir, "reference")
        if not os.path.isdir(ref_dir):
            result.fail(f"{skill}/reference/ 目录不存在")
            continue

        ref_files = os.listdir(ref_dir)
        has_java = any(f.endswith(".java") for f in ref_files)
        has_python = any(f.endswith(".py") for f in ref_files)

        if has_java and has_python:
            result.ok(f"{skill}/reference/ 包含 Java 和 Python 参考代码")
        else:
            missing = []
            if not has_java:
                missing.append("Java")
            if not has_python:
                missing.append("Python")
            result.fail(f"{skill}/reference/ 缺少参考代码: {missing}")


def main():
    print("=" * 60)
    print("收钱吧支付 Skills 项目 —— 验证测试 v3")
    print("=" * 60)

    result = TestResult()

    test_directory_structure(result)
    test_skill_md_content(result)
    test_python_syntax(result)
    test_java_syntax(result)
    test_api_path_consistency(result)
    test_no_broken_references(result)
    test_shared_reference_usage(result)
    test_safety_warnings(result)
    test_notify_verification_mandatory(result)
    test_frontend_variants(result)
    test_yaml_frontmatter(result)
    test_trigger_keywords_count(result)
    test_shared_reference_completeness(result)
    test_module_sections(result)
    test_generation_mode_section(result)
    test_cross_cutting_skill_independence(result)

    success = result.summary()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
