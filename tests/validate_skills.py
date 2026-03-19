#!/usr/bin/env python3
"""
收钱吧支付 Skills 项目验证测试

验证内容：
1. 目录结构完整性 —— 每个 skill 都有 SKILL.md 和 reference 代码
2. SKILL.md 文档格式 —— 包含必要章节
3. Python 参考代码语法检查
4. API 路径一致性 —— SKILL.md 与参考代码中的路径匹配
"""

import os
import re
import sys
import py_compile
import tempfile

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_SKILLS_DIR = os.path.join(PROJECT_ROOT, "sqb-api-skills")

# 预期的 skill 目录列表
EXPECTED_SKILLS = [
    "sqb-activate",
    "sqb-checkin",
    "sqb-pay",
    "sqb-query",
    "sqb-refund",
    "sqb-notify",
]

# SKILL.md 必须包含的章节关键词
REQUIRED_SECTIONS = {
    "sqb-activate": ["激活", "terminal_sn", "terminal_key", "vendor_sn"],
    "sqb-checkin": ["签到", "terminal_sn", "terminal_key"],
    "sqb-pay": ["支付", "client_sn", "total_amount", "dynamic_id", "/upay/v2/pay"],
    "sqb-query": ["查询", "terminal_sn", "/upay/v2/query"],
    "sqb-refund": ["退款", "refund_amount", "refund_request_no", "/upay/v2/refund"],
    "sqb-notify": ["回调", "notify_url", "success"],
}

# API 路径映射（skill -> 预期路径）
EXPECTED_API_PATHS = {
    "sqb-activate": "/terminal/activate",
    "sqb-checkin": "/terminal/checkin",
    "sqb-pay": "/upay/v2/pay",
    "sqb-query": "/upay/v2/query",
    "sqb-refund": "/upay/v2/refund",
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
        print(f"\n{'='*60}")
        print(f"结果: {self.passed}/{total} 通过, {self.failed} 失败")
        if self.errors:
            print(f"\n失败项:")
            for e in self.errors:
                print(f"  - {e}")
        print(f"{'='*60}")
        return self.failed == 0


def test_directory_structure(result):
    """测试 1: 目录结构完整性"""
    print("\n[测试 1] 目录结构完整性")

    for skill in EXPECTED_SKILLS:
        skill_dir = os.path.join(API_SKILLS_DIR, skill)

        # 检查 skill 目录存在
        if os.path.isdir(skill_dir):
            result.ok(f"{skill}/ 目录存在")
        else:
            result.fail(f"{skill}/ 目录不存在")
            continue

        # 检查 SKILL.md 存在
        skill_md = os.path.join(skill_dir, "SKILL.md")
        if os.path.isfile(skill_md):
            result.ok(f"{skill}/SKILL.md 存在")
        else:
            result.fail(f"{skill}/SKILL.md 不存在")

        # 检查 reference 目录存在且有文件
        ref_dir = os.path.join(skill_dir, "reference")
        if os.path.isdir(ref_dir):
            ref_files = os.listdir(ref_dir)
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
        skill_md = os.path.join(API_SKILLS_DIR, skill, "SKILL.md")
        if not os.path.isfile(skill_md):
            result.fail(f"{skill}/SKILL.md 不存在，跳过内容检查")
            continue

        with open(skill_md, "r", encoding="utf-8") as f:
            content = f.read()

        # 检查文件非空
        if len(content) < 100:
            result.fail(f"{skill}/SKILL.md 内容过短 ({len(content)} 字节)")
            continue

        # 检查必要关键词
        missing = [kw for kw in keywords if kw not in content]
        if not missing:
            result.ok(f"{skill}/SKILL.md 包含所有必要关键词")
        else:
            result.fail(f"{skill}/SKILL.md 缺少关键词: {missing}")

        # 检查有 Markdown 标题
        if re.search(r"^#+\s", content, re.MULTILINE):
            result.ok(f"{skill}/SKILL.md 有 Markdown 标题结构")
        else:
            result.fail(f"{skill}/SKILL.md 缺少 Markdown 标题")


def test_python_syntax(result):
    """测试 3: Python 参考代码语法检查"""
    print("\n[测试 3] Python 参考代码语法检查")

    for skill in EXPECTED_SKILLS:
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


def test_java_syntax(result):
    """测试 4: Java 参考代码基本结构检查（不编译，检查结构）"""
    print("\n[测试 4] Java 参考代码结构检查")

    for skill in EXPECTED_SKILLS:
        ref_dir = os.path.join(API_SKILLS_DIR, skill, "reference")
        if not os.path.isdir(ref_dir):
            continue

        for fname in os.listdir(ref_dir):
            if not fname.endswith(".java"):
                continue

            fpath = os.path.join(ref_dir, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()

            # 检查基本 Java 结构
            has_class = bool(re.search(r"\bclass\s+\w+", content))
            has_braces = content.count("{") > 0 and content.count("{") == content.count("}")

            if has_class and has_braces:
                result.ok(f"{skill}/reference/{fname} 结构正确 (class 定义 + 大括号匹配)")
            else:
                issues = []
                if not has_class:
                    issues.append("缺少 class 定义")
                if not has_braces:
                    issues.append(f"大括号不匹配 ({{ ={content.count('{')}, }} ={content.count('}')}")
                result.fail(f"{skill}/reference/{fname} 结构问题: {', '.join(issues)}")


def test_api_path_consistency(result):
    """测试 5: API 路径一致性（SKILL.md vs 参考代码）"""
    print("\n[测试 5] API 路径一致性检查")

    for skill, expected_path in EXPECTED_API_PATHS.items():
        skill_md = os.path.join(API_SKILLS_DIR, skill, "SKILL.md")
        ref_dir = os.path.join(API_SKILLS_DIR, skill, "reference")

        if not os.path.isfile(skill_md):
            continue

        with open(skill_md, "r", encoding="utf-8") as f:
            md_content = f.read()

        # 检查 SKILL.md 中的路径
        if expected_path in md_content:
            result.ok(f"{skill}/SKILL.md 包含正确路径 {expected_path}")
        else:
            result.fail(f"{skill}/SKILL.md 未包含预期路径 {expected_path}")

        # 检查参考代码中的路径
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
            else:
                # 检查是否包含旧路径
                old_path = expected_path.replace("/upay/v2/", "/api/v2/")
                if old_path in code_content:
                    result.fail(f"{skill}/reference/{fname} 仍使用旧路径 {old_path}")
                else:
                    # notify 等没有直接 API 路径的 skill 可跳过
                    pass


def test_no_broken_references(result):
    """测试 6: 检查文档中没有明显的占位符或 TODO"""
    print("\n[测试 6] 占位符/TODO 检查")

    # 使用完整单词匹配，避免 "old_key_xxx" 之类的误报
    placeholder_pattern = re.compile(r'\b(TODO|FIXME|XXX|PLACEHOLDER|TBD)\b', re.IGNORECASE)

    for skill in EXPECTED_SKILLS:
        skill_md = os.path.join(API_SKILLS_DIR, skill, "SKILL.md")
        if not os.path.isfile(skill_md):
            continue

        with open(skill_md, "r", encoding="utf-8") as f:
            content = f.read()

        found = placeholder_pattern.findall(content)
        if not found:
            result.ok(f"{skill}/SKILL.md 无占位符")
        else:
            result.fail(f"{skill}/SKILL.md 包含占位符: {found}")


def main():
    print("=" * 60)
    print("收钱吧支付 Skills 项目 —— 验证测试")
    print("=" * 60)

    result = TestResult()

    test_directory_structure(result)
    test_skill_md_content(result)
    test_python_syntax(result)
    test_java_syntax(result)
    test_api_path_consistency(result)
    test_no_broken_references(result)

    success = result.summary()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
