#!/usr/bin/env python3
"""Export public ChatGPT and Codex shares without browser credentials."""

import argparse
import hashlib
import json
import mimetypes
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


USER_AGENT = "Mozilla/5.0 (compatible; chat-share-export/1.0)"
MAX_DOWNLOAD = 100 * 1024 * 1024
ENQUEUE = re.compile(r'streamController\.enqueue\(("(?:[^"\\]|\\.)*")\)')


class ExportError(Exception):
    pass


def parse_url(url):
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.netloc != "chatgpt.com" or parsed.query or parsed.fragment:
        raise ExportError("仅支持不带查询参数的 https://chatgpt.com 公开分享链接")
    match = re.fullmatch(r"/share/([0-9a-fA-F-]{36})/?", parsed.path)
    if match:
        return "chatgpt", match.group(1)
    match = re.fullmatch(r"/s/(cx_[a-zA-Z0-9_-]+)/?", parsed.path)
    if match:
        return "codex", match.group(1)
    raise ExportError("不支持此链接：需要 /share/<id> 或 /s/cx_<id>")


class SameHostRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self, allow_assets=False):
        self.allow_assets = allow_assets

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urllib.parse.urlsplit(newurl)
        allowed = parsed.netloc == "chatgpt.com" or (
            self.allow_assets and parsed.hostname is not None
            and parsed.hostname.endswith(".oaiusercontent.com")
            and parsed.port in (None, 443) and not parsed.username and not parsed.password
        )
        if parsed.scheme != "https" or not allowed:
            raise ExportError("拒绝跳转到非授权的存储地址")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch(url, allow_assets=False):
    opener = urllib.request.build_opener(SameHostRedirect(allow_assets))
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with opener.open(req, timeout=30) as response:
        data = response.read(MAX_DOWNLOAD + 1)
        if len(data) > MAX_DOWNLOAD:
            raise ExportError("响应超过 100 MiB 限制")
        return data, response.headers.get_content_type()


def decode_table(table, index, active=None):
    if not isinstance(index, int):
        raise ExportError("分享页面数据引用格式异常")
    if index == -5:
        return None
    if index < 0:
        raise ExportError(f"不支持的分享页面特殊引用：{index}")
    if index >= len(table):
        raise ExportError("分享页面数据引用越界")
    active = set() if active is None else active
    if index in active:
        raise ExportError("分享页面数据存在循环引用")
    value = table[index]
    if not isinstance(value, (dict, list)):
        return value
    active.add(index)
    try:
        if isinstance(value, list):
            return [decode_table(table, item, active) for item in value]
        result = {}
        for key, item in value.items():
            if not re.fullmatch(r"_\d+", key):
                raise ExportError("分享页面数据键格式异常")
            name = table[int(key[1:])]
            if not isinstance(name, str):
                raise ExportError("分享页面数据键不是字符串")
            result[name] = decode_table(table, item, active)
        return result
    finally:
        active.remove(index)


def chat_data(html):
    for match in ENQUEUE.finditer(html):
        try:
            stream = json.loads(match.group(1))
            table = json.loads(stream.splitlines()[0])
            if not isinstance(table, list):
                continue
            root = table[0]
            def lookup(obj, name):
                return next(value for key, value in obj.items()
                            if key.startswith("_") and key[1:].isdigit()
                            and table[int(key[1:])] == name)
            loaders = table[lookup(root, "loaderData")]
            route = next(value for key, value in loaders.items()
                         if str(table[int(key[1:])]).startswith("routes/share."))
            response = table[lookup(table[route], "serverResponse")]
            result = decode_table(table, lookup(response, "data"))
            if isinstance(result, dict) and isinstance(result.get("mapping"), dict):
                return result
        except (ValueError, KeyError, IndexError, TypeError, StopIteration, RecursionError):
            continue
    raise ExportError("无法解析普通分享页的对话数据；页面可能已变更或分享不可用")


def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def collect_chat_attachments(value, path="$"):
    found = []
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{path}.{key}"
            if key in ("asset_pointer", "file_id", "attachments") and item:
                found.append({"location": child, "reference": item, "status": "unresolved",
                              "reason": "普通分享页未提供已验证的公开附件下载方式"})
            else:
                found.extend(collect_chat_attachments(item, child))
    elif isinstance(value, list):
        for i, item in enumerate(value):
            found.extend(collect_chat_attachments(item, f"{path}[{i}]"))
    return found


def chat_markdown(data):
    nodes = data.get("linear_conversation")
    if not isinstance(nodes, list):
        raise ExportError("普通分享缺少线性对话，无法保证消息顺序")
    lines = [f"# {data.get('title') or 'ChatGPT 分享'}", ""]
    count = 0
    for node in nodes:
        if not isinstance(node, dict):
            continue
        message = node.get("message")
        if not isinstance(message, dict):
            continue
        role = (message.get("author") or {}).get("role")
        metadata = message.get("metadata") or {}
        if (role not in ("user", "assistant")
                or metadata.get("is_visually_hidden_from_conversation")
                or metadata.get("is_thinking_preamble_message")
                or message.get("recipient") not in (None, "all")):
            continue
        content = message.get("content") or {}
        parts = content.get("parts", [])
        if not isinstance(parts, list) or not parts:
            continue
        lines += [f"## {role}", ""]
        for part in parts:
            lines += [part if isinstance(part, str) else json.dumps(part, ensure_ascii=False, indent=2), ""]
        count += 1
    if not count:
        raise ExportError("普通分享没有可导出的用户或助手消息")
    return "\n".join(lines)


def codex_markdown(data, assets):
    lines = [f"# {data.get('title') or 'Codex 分享'}", ""]
    for number, turn in enumerate(data["turns"], 1):
        lines += [f"## Turn {number}", ""]
        for item in turn.get("items", []):
            kind = item.get("type", "unknown")
            lines += [f"### {kind}", ""]
            remaining = {k: v for k, v in item.items() if k != "type"}
            content = remaining.pop("content", None)
            if content is not None and not isinstance(content, list):
                remaining["content"] = content
                content = []
            for block in content or []:
                if isinstance(block, dict) and block.get("type") == "text":
                    lines += [block.get("text", ""), ""]
                elif isinstance(block, dict) and block.get("type") == "image":
                    ref = block.get("url", "")
                    asset = assets.get(ref)
                    lines += [f"![附件]({asset})" if asset else f"附件未下载：{ref}", ""]
                else:
                    lines += ["```json", json.dumps(block, ensure_ascii=False, indent=2), "```", ""]
            for key in ("text", "summary"):
                if key in remaining:
                    lines += [str(remaining.pop(key)), ""]
            if remaining:
                lines += ["```json", json.dumps(remaining, ensure_ascii=False, indent=2), "```", ""]
    return "\n".join(lines)


def export(url, output):
    kind, identifier = parse_url(url)
    if output.exists():
        raise ExportError(f"输出路径已存在，不会覆盖：{output}")
    base = f"https://chatgpt.com/backend-api/wham/shared_threads/{identifier}"
    raw, content_type = fetch(base if kind == "codex" else url)
    if kind == "codex":
        if content_type != "application/json":
            raise ExportError(f"Codex 接口返回了非 JSON 内容：{content_type}")
        data = json.loads(raw)
        if not isinstance(data, dict) or not isinstance(data.get("turns"), list) or not isinstance(data.get("assets"), dict):
            raise ExportError("Codex JSON 缺少 turns 或 assets")
    else:
        data = chat_data(raw.decode("utf-8"))
    output.mkdir(parents=True)
    save_json(output / "source.json", data)
    manifest = {"source": url, "type": kind, "attachments": [], "warnings": []}
    if kind == "codex":
        assets = {}
        for asset_id in data["assets"]:
            record = {"id": asset_id}
            manifest["attachments"].append(record)
            if not re.fullmatch(r"[a-zA-Z0-9_-]+", asset_id):
                record.update(status="failed", reason="无效的附件 ID")
                continue
            asset_url = f"{base}/assets/{asset_id}"
            try:
                body, mime = fetch(asset_url, allow_assets=True)
                if mime in ("text/html", "application/json"):
                    raise ExportError(f"附件端点返回非文件内容：{mime}")
                extension = mimetypes.guess_extension(mime) or ".bin"
                if extension == ".jpe":
                    extension = ".jpg"
                relative = f"attachments/{asset_id}{extension}"
                (output / "attachments").mkdir(exist_ok=True)
                (output / relative).write_bytes(body)
                record.update(status="downloaded", path=relative, content_type=mime,
                              size=len(body), sha256=hashlib.sha256(body).hexdigest())
                assets[asset_url] = relative
                assets[f"/backend-api/wham/shared_threads/{identifier}/assets/{asset_id}"] = relative
                assets[f"codex:shared-asset/{asset_id}"] = relative
            except (OSError, urllib.error.URLError, ExportError) as error:
                record.update(status="failed", reason=str(error))
        known_references = {
            reference
            for asset_id in data["assets"]
            for reference in (f"codex:shared-asset/{asset_id}", f"{base}/assets/{asset_id}",
                              f"/backend-api/wham/shared_threads/{identifier}/assets/{asset_id}")
        }
        for turn_number, turn in enumerate(data["turns"], 1):
            for item_number, item in enumerate(turn.get("items", []), 1):
                content = item.get("content")
                for block in content if isinstance(content, list) else []:
                    if not isinstance(block, dict) or block.get("type") != "image":
                        continue
                    reference = block.get("url")
                    if not isinstance(reference, str) or reference not in known_references:
                        manifest["attachments"].append({
                            "status": "unresolved", "reference": reference,
                            "location": f"turns[{turn_number}].items[{item_number}]",
                            "reason": "图片引用未对应到共享附件清单",
                        })
        markdown = codex_markdown(data, assets)
    else:
        manifest["attachments"] = collect_chat_attachments(data)
        markdown = chat_markdown(data)
    (output / "conversation.md").write_text(markdown, encoding="utf-8")
    if any(item["status"] != "downloaded" for item in manifest["attachments"]):
        manifest["warnings"].append("部分附件未能下载；请检查 attachments 中的逐项状态。")
    save_json(output / "manifest.json", manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("--out", type=Path, help="不存在的输出目录")
    args = parser.parse_args()
    try:
        _, identifier = parse_url(args.url)
        output = args.out or Path(identifier)
        result = export(args.url, output)
        print(f"导出目录：{output}")
        print(f"附件：{len(result['attachments'])}，警告：{len(result['warnings'])}")
        for warning in result["warnings"]:
            print(f"警告：{warning}", file=sys.stderr)
        return 2 if result["warnings"] else 0
    except (ExportError, OSError, urllib.error.URLError, UnicodeError, json.JSONDecodeError) as error:
        print(f"导出失败：{error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
